# Cloudera 쿼리 엔진 선택 가이드
### — Impala / Hive on Tez / Spark, 언제 무엇을 써야 하나 —

---

## 한 줄 요약

| 엔진 | 한 줄 요약 | 비유 |
|:---|:---|:---|
| **Impala** | 빠른 조회 전용 엔진 | 패스트푸드 — 즉시 나옴, 무거운 건 못 함 |
| **Hive on Tez** | 안정적인 대용량 배치 엔진 | 한식당 — 느리지만 뭐든 다 됨 |
| **Spark** | 빠른 대용량 처리 + 복잡한 로직 | 고급 레스토랑 — 준비 오래 걸리지만 결과가 뛰어남 |

---

## 공통 기반: Hive Metastore

세 엔진 모두 **Hive Metastore**를 공유합니다.

```
┌─────────────────────────────────────────────┐
│              Hive Metastore                 │
│  (테이블 스키마, 위치, 파티션 정보 보관)       │
└────────────┬────────────┬───────────────────┘
             │            │            │
         Impala        Hive(Tez)     Spark
```

Hive Metastore는 **엔진이 아니라 메타데이터 저장소**입니다.
테이블을 어디서 만들든 (Impala로 만들어도, Hive로 만들어도) 모두 같은 Metastore에 등록되어 세 엔진이 공유해서 읽을 수 있습니다.

```sql
-- Impala로 만든 테이블을
CREATE TABLE traffic_demo.traffic_volume (...);

-- Hive에서도 바로 읽을 수 있음
SELECT * FROM traffic_demo.traffic_volume LIMIT 10;

-- Spark에서도 바로 읽을 수 있음
spark.read.table("traffic_demo.traffic_volume")
```

---

### Hive Metastore란 정확히 무엇인가

#### 한 줄 정의

> **HDFS에 저장된 파일에 "이름표"를 붙여주는 저장소**

---

#### 비유로 이해하기

도서관을 생각해봅시다.

```
HDFS                = 도서관 서가 (책이 실제로 꽂혀 있는 곳)
Hive Metastore      = 도서관 목록 카드 (책이 어디 있는지 적어둔 색인)
Impala / Hive / Spark = 책을 꺼내 읽는 사람
```

책(데이터)은 서가(HDFS)에 있습니다.
하지만 어느 칸(경로)에, 어떤 형식(Parquet/CSV)으로, 어떤 순서로 꽂혀 있는지를 기억하는 건 **목록 카드(Metastore)** 입니다.

목록 카드가 없으면 누가 와도 책을 찾을 수 없습니다.
목록 카드만 있고 책이 없으면 빈 칸만 나옵니다.

---

#### 실제로 무엇을 저장하나

Hive Metastore는 내부적으로 **MySQL 또는 PostgreSQL** 같은 관계형 DB에 아래 정보를 저장합니다.

```
테이블명          traffic_demo.traffic_volume
컬럼 목록         collect_date STRING, collect_hour STRING, ...
파일 포맷         PARQUET
실제 데이터 위치   hdfs://namenode/user/root/traffic_demo/input/
파티션 정보        collect_date=2024-01, collect_date=2024-02, ...
```

---

#### 예제로 이해하기

**Step 1. HDFS에 파일이 있는 상태 (아직 Metastore 등록 전)**

```bash
# HDFS 파일 확인
hdfs dfs -ls /user/root/traffic_demo/input/
# → traffic_volume.snappy.parquet 존재

# 하지만 Impala/Hive에서는 아직 모름
impala-shell -q "SELECT * FROM traffic_demo.traffic_volume LIMIT 1;"
# → ERROR: Table does not exist: traffic_demo.traffic_volume
```

파일은 HDFS에 있지만, Metastore에 등록이 안 됐기 때문에 어떤 엔진도 "테이블"로 인식하지 못합니다.

---

**Step 2. Metastore에 등록 (CREATE TABLE)**

```sql
-- Impala로 등록
CREATE EXTERNAL TABLE traffic_demo.traffic_volume
  LIKE PARQUET '/user/root/traffic_demo/input/traffic_volume.snappy.parquet'
  STORED AS PARQUET
  LOCATION '/user/root/traffic_demo/input/';
```

이 순간 Metastore(내부 DB)에 아래 정보가 기록됩니다.

```
테이블명   : traffic_demo.traffic_volume
위치       : /user/root/traffic_demo/input/
포맷       : PARQUET
컬럼       : collect_date STRING, collect_hour STRING, total_volume BIGINT ...
```

---

**Step 3. 어떤 엔진에서도 읽을 수 있음**

```sql
-- Impala에서 조회
impala-shell -q "SELECT COUNT(*) FROM traffic_demo.traffic_volume;"

-- Hive에서 조회 (같은 테이블)
beeline -e "SELECT COUNT(*) FROM traffic_demo.traffic_volume;"
```

```python
# Spark에서 조회 (같은 테이블)
spark.read.table("traffic_demo.traffic_volume").show(5)
```

세 엔진 모두 Metastore에서 위치와 스키마를 읽어온 뒤, **HDFS의 같은 파일**을 직접 읽습니다.

---

#### External Table vs Managed Table

Metastore에 테이블을 등록하는 방식은 두 가지입니다.

```
EXTERNAL TABLE (외부 테이블)
  - HDFS 파일은 그대로 두고, Metastore에 이름표만 붙임
  - DROP TABLE 해도 HDFS 파일은 삭제되지 않음
  - 이 프로젝트에서 사용하는 방식

MANAGED TABLE (관리 테이블)
  - Hive/Impala가 데이터 파일까지 직접 관리
  - DROP TABLE 하면 HDFS 파일도 같이 삭제됨
  - 주의해서 사용해야 함
```

```sql
-- External: 파일 유지
CREATE EXTERNAL TABLE traffic_demo.traffic_volume
  LOCATION '/user/root/traffic_demo/input/';

DROP TABLE traffic_demo.traffic_volume;
-- → Metastore 등록만 삭제, HDFS 파일은 그대로

-- Managed: 파일도 삭제
CREATE TABLE traffic_demo.traffic_volume_managed
  LOCATION '/user/root/traffic_demo/managed/';

DROP TABLE traffic_demo.traffic_volume_managed;
-- → Metastore + HDFS 파일 모두 삭제 ⚠️
```

---

#### DESCRIBE로 Metastore 내용 확인

```sql
-- 컬럼 목록 확인
DESCRIBE traffic_demo.traffic_volume;

-- 위치, 포맷, 파티션 등 상세 정보 확인
DESCRIBE FORMATTED traffic_demo.traffic_volume;
```

```
출력 예시:
# col_name          data_type
collect_date        string
collect_hour        string
total_volume        bigint
...
# Detailed Table Information
Location:           hdfs://namenode/user/root/traffic_demo/input
InputFormat:        org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat
Table Type:         EXTERNAL_TABLE
```

---

## 1. Impala

### 특징

- **전용 데몬(impalad)** 이 항상 메모리에 떠 있어 쿼리 즉시 실행
- 디스크 I/O 없이 메모리 내에서 처리 → 응답 속도 빠름
- `INSERT OVERWRITE`, 복잡한 서브쿼리, UDF 등 **일부 기능 제한**
- Parquet, ORC 포맷에 최적화

### 언제 쓰나

```
✅ 써야 할 때
  - 대시보드, 리포팅 (빠른 응답 필요)
  - 데이터 탐색 (SELECT, GROUP BY, JOIN 조회)
  - DDL 작업 (CREATE TABLE, DROP TABLE, ALTER TABLE)
  - 테이블 통계 수집 (COMPUTE STATS)
  - 소~중간 규모 데이터 조회 (수억 건 이하)

❌ 쓰면 안 될 때
  - 대용량 INSERT / ETL 파이프라인
  - 복잡한 윈도우 함수 + 다중 조인 혼합
  - Python/Scala 로직이 필요한 변환
```

### 실행 방법

```bash
# 대화형
impala-shell -i hdw1.ktwings.dd.io:21050

# 스크립트 실행
impala-shell -i hdw1.ktwings.dd.io:21050 <<EOF
SELECT * FROM traffic_demo.traffic_volume LIMIT 10;
EOF

# 단일 쿼리
impala-shell -i hdw1.ktwings.dd.io:21050 -q "SELECT COUNT(*) FROM traffic_demo.traffic_volume;"
```

### 예제: 테이블 생성 + 조회

```sql
-- DB 생성
CREATE DATABASE IF NOT EXISTS traffic_demo;

-- External Table 생성 (Parquet 스키마 자동 인식)
CREATE EXTERNAL TABLE IF NOT EXISTS traffic_demo.traffic_volume
  LIKE PARQUET '/user/root/traffic_demo/input/traffic_volume.snappy.parquet'
  STORED AS PARQUET
  LOCATION '/user/root/traffic_demo/input/';

-- 통계 수집 (쿼리 성능 향상)
COMPUTE STATS traffic_demo.traffic_volume;

-- 시간대별 집계 조회
SELECT
    collect_hour,
    SUM(total_volume) AS total
FROM traffic_demo.traffic_volume
GROUP BY collect_hour
ORDER BY collect_hour;
```

---

## 2. Hive on Tez

### 특징

- 쿼리를 **Tez DAG(방향성 비순환 그래프)** 작업으로 변환해 YARN에서 실행
- 실행 시작 시 컨테이너 할당 → 시작이 다소 느림 (10~30초)
- `INSERT OVERWRITE`, `INSERT INTO`, 파티셔닝 등 **모든 DML 완전 지원**
- 디스크 기반 처리라 메모리 부족 없이 안정적
- HiveServer2가 항상 떠있어 beeline으로 접속

### 언제 쓰나

```
✅ 써야 할 때
  - 대용량 INSERT / ETL 배치 처리
  - 파티션 관리 (MSCK REPAIR, ALTER TABLE ADD PARTITION)
  - 데이터 정제 및 변환 (Bronze → Silver 등)
  - 안정성이 중요한 야간 배치 파이프라인
  - OOM 위험 없이 처리해야 하는 수십억 건 데이터

❌ 쓰면 안 될 때
  - 빠른 응답이 필요한 대화형 조회
  - 반복 처리에서 성능이 중요한 경우 (→ Spark 권장)
```

### 실행 방법

```bash
# 대화형
beeline -u "jdbc:hive2://hdw1.ktwings.dd.io:10000"

# 스크립트 실행
beeline -u "jdbc:hive2://hdw1.ktwings.dd.io:10000" -f my_script.hql

# Heredoc 방식
beeline -u "jdbc:hive2://hdw1.ktwings.dd.io:10000" <<EOF
SELECT COUNT(*) FROM traffic_demo.traffic_volume;
EOF
```

### 예제: ETL (Raw → 정제 테이블)

```sql
-- 정제 테이블 생성
CREATE TABLE IF NOT EXISTS traffic_demo.traffic_volume_curated (
    collect_date    DATE,
    collect_hour    INT,
    io_code         STRING,
    total_volume    BIGINT,
    time_zone       STRING,
    processed_at    TIMESTAMP
)
STORED AS PARQUET
LOCATION '/user/root/traffic_demo/curated/';

-- Raw → 정제 INSERT (필터 + 변환 + 파생 컬럼)
INSERT OVERWRITE TABLE traffic_demo.traffic_volume_curated
SELECT
    TO_DATE(collect_date, 'yyyyMMdd')   AS collect_date,
    CAST(collect_hour AS INT)           AS collect_hour,
    io_code,
    CAST(total_volume AS BIGINT)        AS total_volume,
    CASE
        WHEN CAST(collect_hour AS INT) BETWEEN 7  AND 9  THEN '출근'
        WHEN CAST(collect_hour AS INT) BETWEEN 17 AND 19 THEN '퇴근'
        WHEN CAST(collect_hour AS INT) BETWEEN 0  AND 5  THEN '심야'
        ELSE '일반'
    END                                 AS time_zone,
    CURRENT_TIMESTAMP                   AS processed_at
FROM traffic_demo.traffic_volume
WHERE
    CAST(total_volume AS BIGINT) > 0
    AND CAST(collect_hour AS INT) BETWEEN 0 AND 23;
```

### 예제: 파티션 테이블

```sql
-- 파티션 테이블 생성
CREATE TABLE IF NOT EXISTS traffic_demo.traffic_volume_partitioned (
    collect_hour    INT,
    io_code         STRING,
    total_volume    BIGINT
)
PARTITIONED BY (collect_date STRING)
STORED AS PARQUET;

-- 파티션 단위 적재
SET hive.exec.dynamic.partition.mode=nonstrict;

INSERT OVERWRITE TABLE traffic_demo.traffic_volume_partitioned
PARTITION (collect_date)
SELECT
    CAST(collect_hour AS INT),
    io_code,
    CAST(total_volume AS BIGINT),
    collect_date
FROM traffic_demo.traffic_volume;
```

---

## 3. Spark

### 특징

- 데이터를 **메모리(RDD/DataFrame)** 에 올려 처리 → 반복 연산에 강함
- spark-submit 실행 시 YARN에서 executor 컨테이너 할당 (시작 30초~2분)
- SQL(spark-sql), Python(PySpark), Scala, R 모두 지원
- ML, 스트리밍, 복잡한 커스텀 로직 가능
- Hive Metastore 연동하면 Hive 테이블 그대로 읽고 씀

### 언제 쓰나

```
✅ 써야 할 때
  - 수십억 건 이상 대용량 고속 처리
  - 반복 처리 (캐시 활용으로 속도 향상)
  - ML 파이프라인 (MLlib)
  - 복잡한 커스텀 로직 (Python/Scala 함수)
  - 스트리밍 처리 (Spark Structured Streaming)
  - 여러 데이터소스 조인 (HDFS + Kafka + HBase 등)

❌ 쓰면 안 될 때
  - 단순한 소규모 ETL (Hive로 충분)
  - 빠른 대화형 조회 (Impala가 더 빠름)
  - 실행 횟수가 많아 오버헤드가 문제가 될 때
```

### 실행 방법

```bash
# spark-sql (SQL만 쓸 때, Hive처럼 사용 가능)
spark-sql --master yarn <<EOF
SELECT collect_hour, SUM(total_volume) FROM traffic_demo.traffic_volume GROUP BY 1;
EOF

# spark-submit (PySpark 스크립트)
spark-submit \
  --master yarn \
  --deploy-mode client \
  --executor-memory 4g \
  --num-executors 4 \
  my_etl.py

# pyspark 대화형 셸
pyspark --master yarn
```

### 예제: PySpark ETL

```python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, LongType

spark = SparkSession.builder \
    .appName("traffic_etl") \
    .enableHiveSupport() \
    .getOrCreate()

# Hive Metastore 테이블 바로 읽기
df = spark.read.table("traffic_demo.traffic_volume")

# 변환
df_curated = (df
    .filter(F.col("total_volume").cast(LongType()) > 0)
    .filter(F.col("collect_hour").cast(IntegerType()).between(0, 23))
    .withColumn("collect_hour", F.col("collect_hour").cast(IntegerType()))
    .withColumn("total_volume", F.col("total_volume").cast(LongType()))
    .withColumn("time_zone",
        F.when(F.col("collect_hour").between(7, 9),   "출근")
         .when(F.col("collect_hour").between(17, 19), "퇴근")
         .when(F.col("collect_hour").between(0, 5),   "심야")
         .otherwise("일반"))
    .withColumn("processed_at", F.current_timestamp())
)

# Hive 테이블로 저장
df_curated.write.mode("overwrite").saveAsTable("traffic_demo.traffic_volume_curated")

print(f"처리 완료: {df_curated.count()} rows")
spark.stop()
```

### 예제: spark-sql (Hive와 동일한 문법)

```bash
spark-sql --master yarn <<EOF

INSERT OVERWRITE TABLE traffic_demo.traffic_volume_curated
SELECT
    TO_DATE(collect_date, 'yyyyMMdd') AS collect_date,
    CAST(collect_hour AS INT)         AS collect_hour,
    io_code,
    CAST(total_volume AS BIGINT)      AS total_volume,
    CASE
        WHEN CAST(collect_hour AS INT) BETWEEN 7  AND 9  THEN '출근'
        WHEN CAST(collect_hour AS INT) BETWEEN 17 AND 19 THEN '퇴근'
        WHEN CAST(collect_hour AS INT) BETWEEN 0  AND 5  THEN '심야'
        ELSE '일반'
    END AS time_zone,
    CURRENT_TIMESTAMP AS processed_at
FROM traffic_demo.traffic_volume
WHERE CAST(total_volume AS BIGINT) > 0;

EOF
```

---

## 엔진별 성능 비교

```
데이터 규모별 권장 엔진

  소규모 (~ 1천만 건)
  ├── 조회       → Impala  ✅
  └── ETL        → Hive    ✅

  중간 (1천만 ~ 1억 건)
  ├── 조회       → Impala  ✅
  └── ETL        → Hive or Spark

  대규모 (1억 건 ~)
  ├── 조회       → Impala (파티션 필터 필수)
  └── ETL        → Spark   ✅
```

| 항목 | Impala | Hive (Tez) | Spark |
|:---|:---:|:---:|:---:|
| 시작 시간 | 즉시 | 10~30초 | 30초~2분 |
| SELECT 속도 | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| INSERT/ETL | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 메모리 안정성 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 커스텀 로직 | ❌ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| ML/스트리밍 | ❌ | ❌ | ⭐⭐⭐⭐⭐ |

---

## 이 프로젝트에서의 역할 분담

```
10_upload.sh          HDFS 업로드
        │
        ▼
20_create_bronze.sh   Impala   → External Table 등록 (DDL)
        │
        ▼
30_create_silver.sh   Hive     → INSERT 변환 (ETL)
        │
        ▼
40_save_result.sh     HDFS     → 결과 저장
        │
        ▼
50_preview.sh         Impala   → 결과 조회 (SELECT)
```

**Impala로 등록 → Hive로 가공 → Impala로 조회** 가 Cloudera의 가장 전형적인 패턴입니다.

---

## 자주 하는 실수

### Impala로 대용량 INSERT 시도

```sql
-- ❌ Impala에서는 느리거나 실패할 수 있음
INSERT INTO traffic_demo.traffic_volume_curated
SELECT ... FROM traffic_demo.traffic_volume;  -- 수억 건

-- ✅ Hive나 Spark 사용
beeline -u "jdbc:hive2://..." <<EOF
INSERT OVERWRITE TABLE ...
EOF
```

### Hive로 대화형 조회

```bash
# ❌ 매번 Tez 컨테이너 뜨는데 10~30초 기다려야 함
beeline -u "jdbc:hive2://..." -e "SELECT * FROM t LIMIT 10;"

# ✅ Impala 사용
impala-shell -i hdw1:21050 -q "SELECT * FROM t LIMIT 10;"
```

### Spark를 단순 쿼리에 사용

```bash
# ❌ 2분 기다려서 SELECT 10건 보는 것은 낭비
spark-sql --master yarn -e "SELECT * FROM t LIMIT 10;"

# ✅ Impala 사용
impala-shell -i hdw1:21050 -q "SELECT * FROM t LIMIT 10;"
```
