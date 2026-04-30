# COPY INTO 완전 가이드

> Databricks SQL에서 S3/ADLS/GCS의 파일을 Delta Table로 적재하는 명령어.
> 핵심 특징: **멱등성(Idempotent)** — 같은 파일을 두 번 실행해도 중복 적재 안 됨.

---

## 1. 언제 사용하는가?

| 상황 | 적합 여부 |
|------|----------|
| S3에 쌓인 parquet/csv/json을 Delta Table로 적재 | ✅ 최적 |
| 매일 증분 파일만 추가 적재 (중복 방지) | ✅ 최적 |
| 스트리밍 실시간 적재 | ❌ Auto Loader 사용 |
| 기존 테이블 간 데이터 이동 | ❌ INSERT INTO SELECT 사용 |
| 복잡한 변환 필요 (JOIN, AGG 등) | ❌ Spark DataFrame 사용 |

**COPY INTO vs INSERT INTO:**
- `COPY INTO`: 파일 → 테이블 (파일 추적으로 중복 방지)
- `INSERT INTO`: 쿼리 결과 → 테이블 (중복 방지 없음)

**COPY INTO vs Auto Loader:**
- `COPY INTO`: 배치성 적재 (수천 개 이하 파일에 효율적)
- `Auto Loader`: 스트리밍 적재 (수백만 파일, 지속적 적재에 효율적)

---

## 2. 기본 문법

```sql
COPY INTO target_table
FROM 'source_path'
FILEFORMAT = format
[FORMAT_OPTIONS (...)]
[COPY_OPTIONS (...)]
```

---

## 3. 지원 파일 포맷

| 포맷 | FILEFORMAT 값 | 비고 |
|------|--------------|------|
| Parquet | `PARQUET` | 스키마 자동 추론, 가장 빠름 |
| CSV | `CSV` | header, delimiter 옵션 필요 |
| JSON | `JSON` | 중첩 구조 지원 |
| AVRO | `AVRO` | 스키마 포함 |
| ORC | `ORC` | Hive 호환 |
| TEXT | `TEXT` | 한 줄 = 한 row |
| BINARYFILE | `BINARYFILE` | 이미지, PDF 등 바이너리 |

---

## 4. 핵심 예제

### 4-1. Parquet 기본 적재 (가장 많이 사용)

```sql
-- S3의 parquet 파일을 Delta Table로 적재
-- 이미 적재된 파일은 자동 스킵 (멱등성)
COPY INTO my_catalog.my_schema.sensor_log
FROM 's3://aws-s3-jimin-test/test/raw_data/'
FILEFORMAT = PARQUET;
```

### 4-2. 특정 파티션만 적재

```sql
-- collect_date=2025-10-01 파티션만 적재
COPY INTO my_catalog.my_schema.sensor_log
FROM 's3://aws-s3-jimin-test/test/raw_data/collect_date=2025-10-01/'
FILEFORMAT = PARQUET;
```

### 4-3. 와일드카드 패턴으로 적재

```sql
-- 2025-10월 파티션만 적재 (패턴 매칭)
COPY INTO my_catalog.my_schema.sensor_log
FROM 's3://aws-s3-jimin-test/test/raw_data/'
FILEFORMAT = PARQUET
PATTERN = 'collect_date=2025-10-*/';
```

### 4-4. CSV 적재 (옵션 지정)

```sql
COPY INTO my_catalog.my_schema.sales_data
FROM 's3://my-bucket/csv-files/'
FILEFORMAT = CSV
FORMAT_OPTIONS (
    'header' = 'true',           -- 첫 줄이 컬럼명
    'inferSchema' = 'true',      -- 타입 자동 추론
    'delimiter' = ',',           -- 구분자
    'encoding' = 'UTF-8',
    'nullValue' = 'NULL',        -- NULL 표현 문자열
    'dateFormat' = 'yyyy-MM-dd'  -- 날짜 파싱 형식
);
```

### 4-5. JSON 적재

```sql
COPY INTO my_catalog.my_schema.event_log
FROM 's3://my-bucket/json-events/'
FILEFORMAT = JSON
FORMAT_OPTIONS (
    'multiLine' = 'true',        -- 여러 줄에 걸친 JSON
    'dateFormat' = 'yyyy-MM-dd'
);
```

### 4-6. 스키마 자동 추론 (테이블 없이 적재)

```sql
-- 테이블이 없어도 파일 스키마로 자동 생성
COPY INTO my_catalog.my_schema.new_table
FROM 's3://my-bucket/data/'
FILEFORMAT = PARQUET
COPY_OPTIONS ('mergeSchema' = 'true');
```

### 4-7. credential 지정 (외부 S3 접근)

```sql
COPY INTO my_catalog.my_schema.external_data
FROM 's3://external-bucket/data/'
  WITH (CREDENTIAL my_aws_credential)
FILEFORMAT = PARQUET;
```

---

## 5. 주요 옵션 정리

### FORMAT_OPTIONS

| 옵션 | 적용 포맷 | 설명 |
|------|----------|------|
| `header` | CSV | 첫 줄이 컬럼명인지 (`true`/`false`) |
| `delimiter` | CSV | 구분자 (기본: `,`) |
| `inferSchema` | CSV, JSON | 타입 자동 추론 (`true`/`false`) |
| `multiLine` | JSON | 여러 줄 JSON 허용 |
| `dateFormat` | ALL | 날짜 파싱 형식 |
| `timestampFormat` | ALL | 타임스탬프 파싱 형식 |
| `encoding` | CSV, JSON | 파일 인코딩 (기본: UTF-8) |
| `nullValue` | CSV | NULL로 처리할 문자열 |
| `mergeSchema` | PARQUET | 스키마 변경 허용 |
| `pathGlobFilter` | ALL | 파일 필터 패턴 |

### COPY_OPTIONS

| 옵션 | 기본값 | 설명 |
|------|-------|------|
| `mergeSchema` | `false` | 새 컬럼 자동 추가 허용 |
| `force` | `false` | `true`면 이미 적재된 파일도 다시 적재 (멱등성 무시) |

---

## 6. 멱등성 (Idempotent) 동작 원리

```
첫 실행: file_001.parquet → 적재 ✅ (신규 파일)
         file_002.parquet → 적재 ✅ (신규 파일)

재실행: file_001.parquet → 스킵 ⏭️ (이미 적재됨)
        file_002.parquet → 스킵 ⏭️ (이미 적재됨)
        file_003.parquet → 적재 ✅ (신규 파일)
```

- Databricks가 내부적으로 적재 완료된 파일 목록을 Delta Table 메타데이터에 기록
- 같은 파일을 다시 만나면 자동으로 스킵
- `force = true` 옵션으로 이 동작을 무시하고 강제 재적재 가능

```sql
-- 강제 재적재 (중복 데이터 발생 가능!)
COPY INTO my_table
FROM 's3://bucket/data/'
FILEFORMAT = PARQUET
COPY_OPTIONS ('force' = 'true');
```

---

## 7. 타겟 테이블 사전 생성

COPY INTO는 기존 테이블에 적재하는 명령이므로, 테이블이 먼저 있어야 함.

```sql
-- 방법 1: 스키마 직접 정의
CREATE TABLE IF NOT EXISTS my_catalog.my_schema.sensor_log (
    equipment_id STRING,
    value DOUBLE,
    collect_date DATE
)
USING DELTA
LOCATION 's3://my-bucket/delta/sensor_log/';

-- 방법 2: 빈 Delta 테이블 생성 후 mergeSchema로 적재
CREATE TABLE IF NOT EXISTS my_catalog.my_schema.sensor_log
USING DELTA;

COPY INTO my_catalog.my_schema.sensor_log
FROM 's3://my-bucket/raw/'
FILEFORMAT = PARQUET
COPY_OPTIONS ('mergeSchema' = 'true');
```

---

## 8. 실전 패턴: 매일 증분 적재 파이프라인

```sql
-- 매일 실행해도 안전 (이미 적재된 파일은 자동 스킵)
-- 새로 추가된 파일만 적재됨

-- Step 1: 테이블 생성 (최초 1회)
CREATE TABLE IF NOT EXISTS catalog.schema.daily_sales (
    order_id STRING,
    amount DECIMAL(10,2),
    order_date DATE,
    collect_date DATE
)
USING DELTA
PARTITIONED BY (collect_date);

-- Step 2: 매일 실행 (스케줄러/워크플로우에 등록)
COPY INTO catalog.schema.daily_sales
FROM 's3://data-lake/sales/raw/'
FILEFORMAT = PARQUET;

-- Step 3: 적재 결과 확인
SELECT collect_date, count(*) as row_count
FROM catalog.schema.daily_sales
GROUP BY collect_date
ORDER BY collect_date DESC
LIMIT 10;
```

---

## 9. 실전 패턴: Python에서 COPY INTO 실행

```python
# Databricks 노트북에서 실행
table_name = "my_catalog.my_schema.sensor_log"
s3_path = "s3://aws-s3-jimin-test/test/raw_data_new/"

spark.sql(f"""
    COPY INTO {table_name}
    FROM '{s3_path}'
    FILEFORMAT = PARQUET
""")

# 결과 확인
display(spark.sql(f"SELECT count(*) FROM {table_name}"))
```

---

## 10. 실전 패턴: 파티션별 병렬 COPY INTO (ThreadPoolExecutor)

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# 여러 파티션을 동시에 COPY INTO 실행
table_name = "my_catalog.my_schema.sensor_log"
base_path = "s3://aws-s3-jimin-test/test/raw_data_new"

# 파티션 목록 조회
partitions = dbutils.fs.ls(base_path + "/")
targets = [p for p in partitions if p.name.startswith("collect_date=")]

def copy_one_partition(p):
    folder = p.name.rstrip("/")
    path = f"{base_path}/{folder}/"
    spark.sql(f"""
        COPY INTO {table_name}
        FROM '{path}'
        FILEFORMAT = PARQUET
    """)
    return folder

total = len(targets)
start = datetime.now()

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(copy_one_partition, p): p for p in targets}
    for i, f in enumerate(as_completed(futures), 1):
        try:
            print(f"[{i}/{total}] {f.result()} ✅")
        except Exception as e:
            print(f"[{i}/{total}] ❌ {e}")

print(f"완료: {(datetime.now() - start).total_seconds():.1f}초")
```

---

## 11. 주의사항 및 제한

| 항목 | 내용 |
|------|------|
| 타겟 테이블 | Delta 테이블만 가능 (Hive, Iceberg 불가) |
| 소스 위치 | External Location 또는 Storage Credential 필요 |
| 파일 크기 | 너무 작은 파일 많으면 느림 (128MB~256MB/파일 권장) |
| 스키마 변경 | `mergeSchema = true` 없으면 새 컬럼 무시됨 |
| Serverless | Serverless 클러스터에서 정상 동작 ✅ |
| 파일 추적 | 파일 경로 기반 (파일 내용이 바뀌어도 같은 경로면 스킵!) |
| 동시 실행 | 같은 테이블에 동시 COPY INTO는 충돌 가능 → 순차 실행 권장 |

---

## 12. 트러블슈팅

### 파일이 적재 안 됨 (스킵됨)
```sql
-- 이미 적재된 것으로 기록된 경우 → force로 재적재
COPY INTO my_table
FROM 's3://bucket/data/'
FILEFORMAT = PARQUET
COPY_OPTIONS ('force' = 'true');
```

### 스키마 불일치 에러
```sql
-- 파일에 새 컬럼이 추가된 경우
COPY INTO my_table
FROM 's3://bucket/data/'
FILEFORMAT = PARQUET
COPY_OPTIONS ('mergeSchema' = 'true');
```

### 파일 인코딩 에러 (CSV)
```sql
COPY INTO my_table
FROM 's3://bucket/csv/'
FILEFORMAT = CSV
FORMAT_OPTIONS (
    'encoding' = 'EUC-KR',     -- 한글 파일
    'header' = 'true'
);
```

### 적재 이력 확인
```sql
-- Delta Table 히스토리에서 COPY INTO 실행 이력 확인
DESCRIBE HISTORY my_catalog.my_schema.sensor_log;
```

---

## 13. COPY INTO vs 다른 적재 방식 비교

| | COPY INTO | Auto Loader | INSERT INTO SELECT | df.write |
|---|---|---|---|---|
| 소스 | 파일 (S3) | 파일 (S3) | 테이블/쿼리 | DataFrame |
| 중복 방지 | ✅ 자동 | ✅ 자동 | ❌ 없음 | ❌ 없음 |
| 스트리밍 | ❌ 배치만 | ✅ 스트리밍 | ❌ 배치만 | ❌ 배치만 |
| 파일 수 성능 | ~수천 개 최적 | 수백만 개 최적 | N/A | N/A |
| SQL 사용 | ✅ | ❌ Python만 | ✅ | ❌ Python만 |
| Serverless | ✅ | ✅ | ✅ | ✅ |
