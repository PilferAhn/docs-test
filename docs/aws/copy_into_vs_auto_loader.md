# COPY INTO vs Auto Loader 비교 가이드

> 출처: [Databricks 공식문서 - COPY INTO](https://docs.databricks.com/en/ingestion/copy-into/index.html), [Auto Loader](https://docs.databricks.com/en/ingestion/auto-loader/index.html) (2026.04 기준)

---

## 1. 핵심 비교 요약

| 항목 | COPY INTO | Auto Loader |
|------|-----------|-------------|
| **타입** | SQL 배치 명령어 | Structured Streaming 소스 (`cloudFiles`) |
| **실행 모델** | 트리거 배치 실행 | 스트리밍 (continuous / triggered micro-batch) |
| **적합 규모** | 수천 개 파일 | 수백만~수십억 개 파일 |
| **처리 속도** | 배치 단위 | 거의 실시간 (초 단위 가능) |
| **인터페이스** | `COPY INTO <table> FROM <path>` | `spark.readStream.format("cloudFiles")` |
| **언어** | SQL, Python, R, Scala | Python, SQL (Declarative Pipelines) |
| **공식 입장** | "legacy"로 분류됨 | **권장 방식** |

---

## 2. Checkpoint (상태 추적) 비교

| 항목 | COPY INTO | Auto Loader |
|------|-----------|-------------|
| **저장 위치** | Delta `_delta_log/` (테이블 내부) | 사용자 지정 `checkpointLocation` (RocksDB) |
| **보존 기간** | 영구 (테이블 존재하는 한) | 영구 (경로 존재하는 한) |
| **추적 방식** | Delta 메타데이터에 적재 파일 기록 | RocksDB key-value store에 파일 메타데이터 저장 |
| **장애 복구** | 재실행 시 자동 skip (멱등성) | checkpoint에서 이어서 재개 |
| **정확히 한 번 보장** | O (idempotent) | O (checkpoint 기반) |

> **COPY INTO**: "files in the source location that have already been loaded are skipped on subsequent runs"
>
> **Auto Loader**: "This key-value store ensures that data is processed exactly once"

---

## 3. 파일 감지 방식 비교

### COPY INTO
- 매 실행마다 소스 경로의 **전체 파일 목록을 스캔**
- 이미 적재한 파일은 메타데이터 비교 후 skip
- 파일 수가 많아지면 스캔 시간과 S3 LIST API 비용 급증

### Auto Loader - 두 가지 모드

| 항목 | Directory Listing (기본) | File Notification (권장) |
|------|------------------------|------------------------|
| **동작** | 입력 디렉토리 LIST 호출로 새 파일 감지 | 클라우드 이벤트(SQS 등)로 새 파일 통보 |
| **설정** | 추가 권한 불필요 | 클라우드 리소스 자동 생성 또는 기존 큐 사용 |
| **성능** | 파일 수에 비례해 느려짐 | 파일 수 무관, 새 파일만 즉시 감지 |
| **적합 규모** | 소~중규모 | 대규모 (수백만 파일/시간) |
| **모드 전환** | 언제든 전환 가능, exactly-once 유지 | 언제든 전환 가능, exactly-once 유지 |

#### File Notification 모드 - 클라우드 리소스

| 클라우드 | 구독 서비스 | 큐 서비스 | 제한 |
|---------|-----------|----------|------|
| AWS S3 | SNS | SQS | 버킷당 100개 |
| Azure ADLS | Event Grid | Queue Storage | 스토리지 계정당 500개 |
| GCP GCS | Pub/Sub | Pub/Sub | 버킷당 100개 |

#### File Notification의 SQS 보존 기간 이슈

| 상황 | 결과 |
|------|------|
| 스트림 정상 가동 중 | 문제 없음 - 이벤트 즉시 소비 |
| 스트림 수일간 중단 | SQS 메시지 만료(기본 4일, 최대 14일) → 이벤트 유실 가능 |
| 7일 이상 미실행 | file events 캐시 만료 → Directory Listing으로 fallback |

**안전장치**: `cloudFiles.backfillInterval` 설정으로 주기적 전체 스캔 → 누락 방지

> File Notification을 쓰는 이유: **대규모 환경에서 Directory Listing이 너무 느리고 비싸기 때문**
>
> | 시나리오 | Directory Listing | File Notification |
> |---------|-------------------|-------------------|
> | 파일 100만 개일 때 | LIST API 1,000회 호출 (느림, 비쌈) | 새 파일 이벤트 1건만 수신 |
> | 감지 속도 | 폴링 주기에 의존 (초~분) | 거의 실시간 |
> | S3 API 비용 | LIST 호출 누적 → 비용 증가 | 이벤트 기반 → 비용 거의 없음 |

---

## 4. 스키마 진화 (Schema Evolution) 비교

| 항목 | COPY INTO | Auto Loader |
|------|-----------|-------------|
| **스키마 추론** | `FORMAT_OPTIONS ('mergeSchema' = 'true')` | `cloudFiles.inferColumnTypes` |
| **스키마 진화** | 기본적 (mergeSchema) | 고급 (inference, evolution, hints) |
| **진화 모드** | 없음 | `addNewColumns`, `failOnNewColumns`, `rescue`, `none` |
| **Rescued Data Column** | **미지원** | **기본 지원** (파싱 실패 데이터 자동 보존) |
| **스키마 힌트** | 없음 | `cloudFiles.schemaHints`로 타입 오버라이드 가능 |

> Databricks 공식: "COPY INTO (legacy) does not support the rescued data column because you cannot manually set the schema using COPY INTO."

---

## 5. 공식 권장 기준: 언제 무엇을 쓸까?

### COPY INTO가 적합한 경우
- 시간이 지나면서 **수천 개** 수준의 파일 적재
- **Ad-hoc** 또는 일회성 데이터 로드
- 특정 파일만 **재적재**해야 할 때 (subset reprocessing이 더 쉬움)
- 간단한 SQL 명령어로 빠르게 적재하고 싶을 때

### Auto Loader가 적합한 경우
- 시간이 지나면서 **수백만 개 이상**의 파일 적재
- **실시간/준실시간** 수집이 필요할 때
- 스키마가 **자주 변경**될 때
- **운영 환경** 파이프라인 (항상 실행되는 streaming job)
- 140TB 이상의 **대규모 데이터** 환경

> 공식문서: "If you're going to ingest files in the order of thousands over time, you can use COPY INTO. If you are expecting files in the order of millions or more over time, use Auto Loader."

---

## 6. 대규모 환경 고려사항 (140TB+ 시나리오)

### 파일 크기가 핵심

| 파일 크기 | 140TB 기준 파일 수 | 평가 |
|----------|-------------------|------|
| 50행 (~수KB) | 수십억 개 | S3 LIST만 수시간, **사용 불가** |
| 10MB | 1,400만 개 | 느리고 비용 높음 |
| 128MB~1GB **(권장)** | 14만~110만 개 | **최적** |

### 140TB 환경 권장 전략

| 항목 | 권장 | 이유 |
|------|-----|------|
| 파일 크기 | 128MB~1GB | Spark 읽기 최적 단위, S3 API 호출 최소화 |
| 포맷 | Delta Lake | OPTIMIZE/VACUUM/Z-ORDER, ACID, time travel |
| 적재 방식 | **Auto Loader (File Notification)** | Directory Listing은 수백만 파일 스캔에 수십 분 소요 |
| 파티셔닝 | 과도한 파티셔닝 금지 | 날짜까지는 OK, 날짜/시간/코드 조합은 폴더 폭발 |
| 스토리지 | S3 Intelligent-Tiering | 오래된 데이터 자동으로 저렴한 tier로 이동 |
| 쿼리 최적화 | Liquid Clustering 또는 Z-ORDER | 파티션 pruning + 파일 내 데이터 정렬 |

### S3 비용 추정 (ap-northeast-2 기준)

| 항목 | 월 비용 |
|------|--------|
| S3 Standard 140TB 저장 | ~$3,200/월 |
| S3 Intelligent-Tiering | ~$2,500/월 (접근 패턴에 따라) |
| S3 API 호출 (PUT/GET) | 파일 수에 비례 — 파일 클수록 저렴 |

---

## 7. 코드 예시 비교

### COPY INTO

```sql
-- 기본 사용
COPY INTO traffic.dev.traffic_bronze
FROM 's3://my-bucket/raw/traffic/'
FILEFORMAT = PARQUET;

-- 옵션 포함
COPY INTO traffic.dev.traffic_bronze
FROM 's3://my-bucket/raw/traffic/'
FILEFORMAT = PARQUET
FORMAT_OPTIONS ('mergeSchema' = 'true')
COPY_OPTIONS ('mergeSchema' = 'true');

-- 강제 재적재
COPY INTO traffic.dev.traffic_bronze
FROM 's3://my-bucket/raw/traffic/'
FILEFORMAT = PARQUET
COPY_OPTIONS ('force' = 'true');
```

### Auto Loader

```python
# 기본 사용
(spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "parquet")
    .option("cloudFiles.schemaLocation", "/checkpoints/traffic/schema")
    .load("s3://my-bucket/raw/traffic/")
    .writeStream
    .option("checkpointLocation", "/checkpoints/traffic/cp")
    .trigger(availableNow=True)  # 배치처럼 실행 후 종료
    .toTable("traffic.dev.traffic_bronze")
)

# File Notification 모드 + 스키마 진화
(spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "parquet")
    .option("cloudFiles.useNotifications", "true")      # File Notification 모드
    .option("cloudFiles.inferColumnTypes", "true")       # 타입 자동 추론
    .option("cloudFiles.schemaEvolutionMode", "addNewColumns")  # 새 컬럼 자동 추가
    .option("cloudFiles.schemaLocation", "/checkpoints/traffic/schema")
    .option("cloudFiles.backfillInterval", "1 day")      # 누락 방지 주기적 스캔
    .load("s3://my-bucket/raw/traffic/")
    .writeStream
    .option("checkpointLocation", "/checkpoints/traffic/cp")
    .option("mergeSchema", "true")
    .trigger(availableNow=True)
    .toTable("traffic.dev.traffic_bronze")
)
```

---

## 8. 주요 Auto Loader 옵션 정리

| 옵션 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `cloudFiles.format` | String | (필수) | 파일 포맷: parquet, json, csv, avro, orc, text, xml |
| `cloudFiles.includeExistingFiles` | Boolean | true | 첫 실행 시 기존 파일 포함 여부 |
| `cloudFiles.maxFilesPerTrigger` | Integer | 1000 | 트리거당 최대 파일 수 |
| `cloudFiles.maxBytesPerTrigger` | String | None | 트리거당 최대 바이트 (예: "10g") |
| `cloudFiles.inferColumnTypes` | Boolean | false | 정확한 컬럼 타입 추론 |
| `cloudFiles.schemaEvolutionMode` | String | addNewColumns/none | 스키마 진화 모드 |
| `cloudFiles.schemaLocation` | String | (추론 시 필수) | 추론된 스키마 저장 경로 |
| `cloudFiles.schemaHints` | String | None | 스키마 힌트 (타입 오버라이드) |
| `cloudFiles.useNotifications` | Boolean | false | File Notification 모드 (classic) |
| `cloudFiles.useManagedFileEvents` | Boolean | false | File Events 모드 (권장, DBR 14.3+) |
| `cloudFiles.backfillInterval` | String | None | 주기적 전체 스캔 간격 |
| `cloudFiles.allowOverwrites` | Boolean | false | 파일 변경 시 덮어쓰기 허용 |

### 소스 파일 정리 옵션 (DBR 16.4+)

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `cloudFiles.cleanSource` | OFF | OFF / DELETE / MOVE |
| `cloudFiles.cleanSource.retentionDuration` | 30 days | 정리 전 대기 시간 (DELETE는 최소 7일) |
| `cloudFiles.cleanSource.moveDestination` | None | MOVE 시 아카이브 경로 |

---

## 9. 최종 판단 가이드

```
파일 수천 개 이하 + 배치 + 단순 스키마
  → COPY INTO ✅

파일 수만 개 이상 + 실시간 + 스키마 변경 가능
  → Auto Loader ✅

140TB+ 대규모 운영 환경
  → Auto Loader (File Notification) ✅✅✅
```

| 판단 기준 | COPY INTO | Auto Loader |
|----------|:---------:|:-----------:|
| 파일 수천 개 | **O** | O |
| 파일 수백만 개 | X | **O** |
| 실시간 수집 | X | **O** |
| 스키마 자주 변경 | △ | **O** |
| 특정 파일 재적재 | **O** | △ |
| SQL만 사용 | **O** | △ (Streaming Table) |
| 설정 간편함 | **O** | △ |
| 운영 환경 권장 | △ | **O** |

> **Databricks 공식 입장**: Auto Loader를 권장하며, COPY INTO는 문서에서 "legacy"로 분류됨.
> 단, 소규모 ad-hoc 적재나 특정 파일 재처리 시에는 COPY INTO가 여전히 유용.
