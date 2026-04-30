# Auto Loader 완전 가이드

> Databricks의 스트리밍 파일 적재 엔진.
> S3/ADLS/GCS에 새 파일이 도착하면 **자동으로 감지하여 Delta Table에 적재**.
> 핵심 특징: 수백만 파일도 효율적으로 처리, 정확히 한 번(exactly-once) 적재 보장.

---

## 1. 언제 사용하는가?

| 상황 | 적합 여부 |
|------|----------|
| S3에 지속적으로 파일이 도착 (매시간/매분) | ✅ 최적 |
| 수십만~수백만 파일 증분 적재 | ✅ 최적 |
| 스키마가 시간이 지나면서 변경됨 | ✅ 스키마 진화 자동 지원 |
| 일회성 배치 적재 (파일 수천 개 이하) | ❌ COPY INTO가 간단 |
| SQL만으로 적재하고 싶음 | ❌ Python 필수 (Auto Loader는 PySpark API) |
| 실시간 이벤트 스트리밍 (Kafka 등) | ❌ Structured Streaming + Kafka 사용 |

**Auto Loader vs COPY INTO:**

| | Auto Loader | COPY INTO |
|---|---|---|
| 방식 | 스트리밍 (지속 실행 또는 trigger once) | 배치 (실행할 때마다 1회) |
| 파일 감지 | S3 이벤트 알림 또는 디렉토리 리스팅 | 매 실행 시 전체 리스팅 |
| 대규모 파일 | 수백만 개도 효율적 | 수천 개까지 효율적 |
| 스키마 진화 | 자동 지원 | `mergeSchema` 옵션 필요 |
| 언어 | Python (PySpark) | SQL 또는 Python |
| 체크포인트 | 별도 경로에 저장 | Delta 메타데이터에 기록 |

---

## 2. 동작 원리

```
┌─────────────────────────────────────────────────────────────┐
│                    Auto Loader 파이프라인                      │
│                                                             │
│  [S3 버킷]                                                   │
│  새 파일 도착 ─────→ [파일 감지]  ─────→ [Delta Table]         │
│                      │                                      │
│                      ├─ 방법 1: Directory Listing (기본)      │
│                      │   매 트리거마다 S3 ls 호출              │
│                      │   설정 간단, 파일 적을 때 적합           │
│                      │                                      │
│                      └─ 방법 2: File Notification            │
│                          S3 Event → SQS → Auto Loader       │
│                          대규모 파일에 효율적 (ls 불필요)       │
│                                                             │
│  [체크포인트]                                                 │
│  어디까지 읽었는지 기록 → 재시작해도 중복 없음                    │
└─────────────────────────────────────────────────────────────┘
```

### 파일 감지 모드 비교

| | Directory Listing | File Notification |
|---|---|---|
| 설정 | 없음 (기본값) | S3 Event + SQS 설정 필요 |
| 파일 감지 속도 | 트리거 간격마다 | 거의 실시간 |
| S3 API 비용 | 파일 많으면 LIST 비용 증가 | 이벤트 기반이라 저비용 |
| 적합 상황 | 파일 수만 개 이하 | 파일 수십만 개 이상 |
| `cloudFiles.useNotifications` | `false` (기본) | `true` |

---

## 3. 기본 문법

```python
# 스트리밍 읽기 (Auto Loader)
df = (spark.readStream
    .format("cloudFiles")                    # Auto Loader 포맷
    .option("cloudFiles.format", "parquet")  # 소스 파일 포맷
    .option("cloudFiles.schemaLocation", schema_path)  # 스키마 저장 위치
    .load(source_path)                       # 소스 경로
)

# 스트리밍 쓰기 (Delta Table)
(df.writeStream
    .option("checkpointLocation", checkpoint_path)  # 체크포인트 위치
    .trigger(availableNow=True)              # 트리거 모드
    .toTable(target_table)                   # 타겟 Delta Table
)
```

---

## 4. 트리거 모드

| 트리거 | 설명 | 용도 |
|--------|------|------|
| `trigger(availableNow=True)` | 현재 있는 모든 신규 파일 처리 후 종료 | **배치 잡 (가장 많이 사용)** |
| `trigger(processingTime="1 minute")` | 1분마다 체크하며 지속 실행 | 준실시간 적재 |
| `trigger(once=True)` | 한 배치만 처리 후 종료 (레거시) | `availableNow`로 대체됨 |
| 트리거 미지정 | 가능한 빨리 계속 처리 | 실시간 스트리밍 |

**`availableNow=True` vs `once=True`:**
- `once=True`: 한 번의 마이크로 배치만 실행 (일부 파일 남을 수 있음)
- `availableNow=True`: 모든 미처리 파일을 여러 마이크로 배치로 처리 후 종료 (권장)

---

## 5. 핵심 예제

### 5-1. Parquet 기본 적재 (가장 많이 사용)

```python
source_path = "s3://aws-s3-jimin-test/test/raw_data_new/"
checkpoint_path = "s3://aws-s3-jimin-test/test/_checkpoints/sensor_log/"
schema_path = "s3://aws-s3-jimin-test/test/_schemas/sensor_log/"
target_table = "my_catalog.my_schema.sensor_log"

# 읽기: S3에서 새 parquet 파일 감지
df = (spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "parquet")
    .option("cloudFiles.schemaLocation", schema_path)
    .load(source_path)
)

# 쓰기: Delta Table에 적재
(df.writeStream
    .option("checkpointLocation", checkpoint_path)
    .trigger(availableNow=True)
    .toTable(target_table)
)
```

### 5-2. CSV 적재 (옵션 지정)

```python
df = (spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "csv")
    .option("cloudFiles.schemaLocation", schema_path)
    .option("header", "true")
    .option("delimiter", ",")
    .option("encoding", "UTF-8")
    .option("nullValue", "NULL")
    .load("s3://my-bucket/csv-files/")
)

(df.writeStream
    .option("checkpointLocation", checkpoint_path)
    .trigger(availableNow=True)
    .toTable("my_catalog.my_schema.csv_table")
)
```

### 5-3. JSON 적재 (중첩 구조)

```python
df = (spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "json")
    .option("cloudFiles.schemaLocation", schema_path)
    .option("multiLine", "true")
    .load("s3://my-bucket/json-events/")
)

(df.writeStream
    .option("checkpointLocation", checkpoint_path)
    .option("mergeSchema", "true")
    .trigger(availableNow=True)
    .toTable("my_catalog.my_schema.events")
)
```

### 5-4. 스키마 진화 (Schema Evolution)

```python
# 새 컬럼이 추가된 파일이 들어와도 자동 처리
df = (spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "parquet")
    .option("cloudFiles.schemaLocation", schema_path)
    .option("cloudFiles.schemaEvolutionMode", "addNewColumns")  # 새 컬럼 자동 추가
    .load(source_path)
)

(df.writeStream
    .option("checkpointLocation", checkpoint_path)
    .option("mergeSchema", "true")  # Delta Table에도 스키마 변경 허용
    .trigger(availableNow=True)
    .toTable(target_table)
)
```

**스키마 진화 모드:**

| 모드 | 설명 |
|------|------|
| `addNewColumns` | 새 컬럼 자동 추가 (기본값) |
| `rescue` | 파싱 불가한 데이터를 `_rescued_data` 컬럼에 보관 |
| `failOnNewColumns` | 새 컬럼 발견 시 에러 발생 (엄격 모드) |
| `none` | 스키마 변경 무시 |

### 5-5. 스키마 힌트 (타입 강제 지정)

```python
# 자동 추론이 부정확할 때 특정 컬럼 타입을 강제
df = (spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "csv")
    .option("cloudFiles.schemaLocation", schema_path)
    .option("cloudFiles.schemaHints",
            "order_id STRING, amount DECIMAL(10,2), order_date DATE")
    .option("header", "true")
    .load("s3://my-bucket/sales/")
)
```

### 5-6. File Notification 모드 (대규모 파일)

```python
# S3 Event Notification + SQS 사용
# 사전 준비: S3 버킷에 이벤트 알림 → SQS 큐 연결 필요
df = (spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "parquet")
    .option("cloudFiles.useNotifications", "true")  # 이벤트 모드 활성화
    .option("cloudFiles.region", "ap-northeast-2")  # AWS 리전
    # SQS 자동 설정 (Databricks가 알아서 생성)
    # 또는 기존 SQS 지정:
    # .option("cloudFiles.queueUrl", "https://sqs.ap-northeast-2.amazonaws.com/123456/my-queue")
    .option("cloudFiles.schemaLocation", schema_path)
    .load(source_path)
)
```

### 5-7. 변환 적용 후 적재

```python
from pyspark.sql.functions import col, current_timestamp, input_file_name

df = (spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "parquet")
    .option("cloudFiles.schemaLocation", schema_path)
    .load(source_path)
)

# 변환: 메타데이터 컬럼 추가
transformed = (df
    .withColumn("_ingested_at", current_timestamp())       # 적재 시각
    .withColumn("_source_file", input_file_name())         # 원본 파일 경로
    .filter(col("value").isNotNull())                      # NULL 필터링
)

(transformed.writeStream
    .option("checkpointLocation", checkpoint_path)
    .trigger(availableNow=True)
    .toTable(target_table)
)
```

### 5-8. 파티션 컬럼 포함 적재

```python
# S3 경로: s3://bucket/data/collect_date=2025-10-01/file.parquet
# → collect_date를 자동으로 컬럼으로 추출

df = (spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "parquet")
    .option("cloudFiles.schemaLocation", schema_path)
    .option("cloudFiles.partitionColumns", "collect_date")  # 경로에서 파티션 추출
    .load("s3://aws-s3-jimin-test/test/raw_data_new/")
)

(df.writeStream
    .option("checkpointLocation", checkpoint_path)
    .partitionBy("collect_date")  # Delta Table에도 파티션 유지
    .trigger(availableNow=True)
    .toTable(target_table)
)
```

### 5-9. 준실시간 지속 적재 (매 1분)

```python
# 종료하지 않고 계속 실행 — 새 파일 도착 시 1분 내 적재
query = (df.writeStream
    .option("checkpointLocation", checkpoint_path)
    .trigger(processingTime="1 minute")  # 1분마다 체크
    .toTable(target_table)
)

# 스트림 상태 확인
query.status
query.lastProgress

# 스트림 중지
query.stop()
```

---

## 6. 주요 옵션 정리

### cloudFiles 옵션 (readStream)

| 옵션 | 기본값 | 설명 |
|------|-------|------|
| `cloudFiles.format` | (필수) | 소스 파일 포맷: parquet, csv, json, avro, orc, text, binaryFile |
| `cloudFiles.schemaLocation` | (필수) | 추론된 스키마 저장 경로 |
| `cloudFiles.useNotifications` | `false` | File Notification 모드 활성화 |
| `cloudFiles.region` | (자동) | AWS 리전 (notification 모드 시) |
| `cloudFiles.schemaEvolutionMode` | `addNewColumns` | 스키마 변경 처리 방식 |
| `cloudFiles.schemaHints` | 없음 | 컬럼 타입 강제 지정 |
| `cloudFiles.partitionColumns` | 없음 | 경로에서 추출할 파티션 컬럼 |
| `cloudFiles.maxFilesPerTrigger` | 1000 | 트리거당 최대 처리 파일 수 |
| `cloudFiles.maxBytesPerTrigger` | 없음 | 트리거당 최대 처리 바이트 |
| `cloudFiles.includeExistingFiles` | `true` | 기존 파일도 처리할지 여부 |
| `cloudFiles.validateOptions` | `true` | 옵션 유효성 검증 |

### writeStream 옵션

| 옵션 | 설명 |
|------|------|
| `checkpointLocation` | (필수) 체크포인트 저장 경로 — 재시작 시 이어서 처리 |
| `mergeSchema` | 스키마 변경 허용 (`true`/`false`) |
| `partitionBy` | Delta Table 파티션 컬럼 |

---

## 7. 체크포인트 동작 원리

```
체크포인트 경로: s3://bucket/_checkpoints/my_stream/
├── offsets/     ← 어떤 파일까지 읽었는지 기록
├── commits/     ← 어떤 배치까지 커밋했는지 기록
├── metadata     ← 스트림 메타데이터
└── sources/     ← 소스 상태 정보
```

**핵심 규칙:**
- 체크포인트 경로는 스트림당 고유해야 함 (공유 금지)
- 체크포인트를 삭제하면 처음부터 다시 적재 (중복 발생!)
- 소스 경로를 변경하면 새 체크포인트 필요
- 체크포인트가 있으면 재시작해도 이어서 처리 (exactly-once 보장)

```python
# ❌ 잘못된 사용: 체크포인트 공유
stream_1.option("checkpointLocation", "s3://bucket/cp/shared/")  # 충돌!
stream_2.option("checkpointLocation", "s3://bucket/cp/shared/")  # 충돌!

# ✅ 올바른 사용: 스트림마다 별도 체크포인트
stream_1.option("checkpointLocation", "s3://bucket/cp/stream_1/")
stream_2.option("checkpointLocation", "s3://bucket/cp/stream_2/")
```

---

## 8. 실전 패턴: 완전한 파이프라인 (복붙용)

```python
from pyspark.sql.functions import current_timestamp, input_file_name

# ============================================================
# 설정
# ============================================================
TABLE_NAME = "my_catalog.my_schema.sensor_log"
SOURCE_PATH = "s3://aws-s3-jimin-test/test/raw_data_new/"
CHECKPOINT_PATH = "s3://aws-s3-jimin-test/test/_checkpoints/sensor_log/"
SCHEMA_PATH = "s3://aws-s3-jimin-test/test/_schemas/sensor_log/"

# ============================================================
# 1. 읽기: Auto Loader로 S3에서 새 파일 감지
# ============================================================
raw_df = (spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "parquet")
    .option("cloudFiles.schemaLocation", SCHEMA_PATH)
    .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
    .option("cloudFiles.partitionColumns", "collect_date")
    .load(SOURCE_PATH)
)

# ============================================================
# 2. 변환: 메타데이터 추가
# ============================================================
transformed_df = (raw_df
    .withColumn("_ingested_at", current_timestamp())
    .withColumn("_source_file", input_file_name())
)

# ============================================================
# 3. 쓰기: Delta Table에 적재 (배치 모드)
# ============================================================
query = (transformed_df.writeStream
    .option("checkpointLocation", CHECKPOINT_PATH)
    .option("mergeSchema", "true")
    .partitionBy("collect_date")
    .trigger(availableNow=True)
    .toTable(TABLE_NAME)
)

# 완료 대기
query.awaitTermination()
print(f"적재 완료: {TABLE_NAME}")

# ============================================================
# 4. 검증
# ============================================================
count = spark.table(TABLE_NAME).count()
print(f"전체 행 수: {count:,}")

display(
    spark.sql(f"""
        SELECT collect_date, count(*) as rows
        FROM {TABLE_NAME}
        GROUP BY collect_date
        ORDER BY collect_date DESC
        LIMIT 10
    """)
)
```

---

## 9. 실전 패턴: 여러 테이블 동시 적재

```python
# 여러 소스를 각각 별도 Auto Loader로 적재
tables = [
    {
        "name": "catalog.schema.sensor_log",
        "source": "s3://bucket/raw/sensor_log/",
        "format": "parquet",
    },
    {
        "name": "catalog.schema.event_log",
        "source": "s3://bucket/raw/event_log/",
        "format": "json",
    },
    {
        "name": "catalog.schema.sales",
        "source": "s3://bucket/raw/sales/",
        "format": "csv",
    },
]

queries = []

for table in tables:
    checkpoint = f"s3://bucket/_checkpoints/{table['name'].split('.')[-1]}/"
    schema_loc = f"s3://bucket/_schemas/{table['name'].split('.')[-1]}/"

    df = (spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", table["format"])
        .option("cloudFiles.schemaLocation", schema_loc)
        .load(table["source"])
    )

    q = (df.writeStream
        .option("checkpointLocation", checkpoint)
        .option("mergeSchema", "true")
        .trigger(availableNow=True)
        .toTable(table["name"])
    )
    queries.append(q)
    print(f"시작: {table['name']}")

# 모든 스트림 완료 대기
for q in queries:
    q.awaitTermination()

print("전체 적재 완료")
```

---

## 10. 실전 패턴: Databricks Workflow 스케줄링

```python
# Databricks Job/Workflow에서 매시간 실행되는 노트북
# availableNow=True 사용 → 신규 파일만 처리 후 자동 종료

# 노트북 파라미터 (Widgets)
dbutils.widgets.text("table_name", "catalog.schema.sensor_log")
dbutils.widgets.text("source_path", "s3://bucket/raw/sensor_log/")

table_name = dbutils.widgets.get("table_name")
source_path = dbutils.widgets.get("source_path")
checkpoint = f"s3://bucket/_checkpoints/{table_name.split('.')[-1]}/"
schema_loc = f"s3://bucket/_schemas/{table_name.split('.')[-1]}/"

df = (spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "parquet")
    .option("cloudFiles.schemaLocation", schema_loc)
    .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
    .load(source_path)
)

query = (df.writeStream
    .option("checkpointLocation", checkpoint)
    .option("mergeSchema", "true")
    .trigger(availableNow=True)
    .toTable(table_name)
)

query.awaitTermination()

# 적재 결과 출력
new_rows = query.lastProgress.get("numInputRows", 0) if query.lastProgress else 0
print(f"적재 완료: {table_name} | 신규 행: {new_rows}")
```

---

## 11. 주의사항 및 제한

| 항목 | 내용 |
|------|------|
| 타겟 테이블 | Delta Table만 가능 |
| 체크포인트 | 절대 삭제하지 말 것 (삭제 시 전체 재적재, 중복 발생) |
| 소스 경로 변경 | 체크포인트도 새로 만들어야 함 |
| 파일 삭제 | 소스에서 파일을 삭제해도 테이블에는 영향 없음 |
| 파일 수정 | 이미 적재된 파일이 수정되어도 재적재 안 됨 (새 파일만 감지) |
| Serverless | ✅ 정상 동작 |
| Unity Catalog | ✅ 3-level namespace 지원 |
| 동시 실행 | 같은 체크포인트로 2개 스트림 실행 시 충돌 |

---

## 12. 트러블슈팅

### 스키마 추론 실패
```python
# 스키마 힌트로 문제 컬럼 타입 강제 지정
.option("cloudFiles.schemaHints", "amount DOUBLE, date_col DATE")
```

### 파일이 감지 안 됨
```python
# 1. 기존 파일 포함 여부 확인
.option("cloudFiles.includeExistingFiles", "true")

# 2. 체크포인트 확인 (이미 처리된 파일은 스킵됨)
# 체크포인트 삭제 후 재시작하면 전체 재처리 (주의: 중복!)
```

### 적재 속도가 느림
```python
# 트리거당 파일 수 제한 늘리기
.option("cloudFiles.maxFilesPerTrigger", "10000")

# 또는 바이트 기반 제한
.option("cloudFiles.maxBytesPerTrigger", "10g")
```

### 특정 파일 필터링
```python
# 특정 확장자만 처리
.option("pathGlobFilter", "*.parquet")

# 특정 경로 패턴만 처리
.option("cloudFiles.pathFilter", "collect_date=2025-10-*")
```

### 에러 파일 건너뛰기 (Rescue)
```python
# 파싱 실패한 레코드를 _rescued_data 컬럼에 보관
df = (spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "json")
    .option("cloudFiles.schemaLocation", schema_path)
    .option("cloudFiles.schemaEvolutionMode", "rescue")  # 에러 데이터 보관
    .load(source_path)
)

# 나중에 rescue된 데이터 확인
spark.sql(f"""
    SELECT _rescued_data, count(*)
    FROM {target_table}
    WHERE _rescued_data IS NOT NULL
    GROUP BY _rescued_data
""")
```

### 체크포인트 리셋 (전체 재적재)

```python
# ⚠️ 주의: 중복 데이터 발생 가능!
# 1. 기존 체크포인트 삭제
dbutils.fs.rm(checkpoint_path, recurse=True)

# 2. (선택) 기존 테이블 데이터도 삭제
spark.sql(f"TRUNCATE TABLE {target_table}")

# 3. Auto Loader 재시작 → 전체 파일 다시 적재
```

---

## 13. Auto Loader vs COPY INTO 선택 플로우차트

```
파일이 지속적으로 도착하는가?
├── YES → 파일 수가 수만 개 이상인가?
│         ├── YES → Auto Loader (File Notification 모드)
│         └── NO  → Auto Loader (Directory Listing 모드)
└── NO  → 일회성/간헐적 적재인가?
          ├── YES → COPY INTO
          └── NO  → Auto Loader (availableNow=True, 스케줄링)
```

---

## 14. 비용 최적화 팁

| 팁 | 설명 |
|----|------|
| `availableNow=True` 사용 | 지속 실행 클러스터 비용 절약 (처리 후 종료) |
| `maxFilesPerTrigger` 조정 | 너무 크면 메모리 부족, 너무 작으면 잦은 커밋 |
| File Notification 모드 | 대규모 파일에서 S3 LIST API 비용 절감 |
| Serverless 클러스터 | 실행 시간만 과금, 유휴 비용 없음 |
| 소스 파일 크기 128MB~256MB | 너무 작은 파일은 오버헤드 큼 |
