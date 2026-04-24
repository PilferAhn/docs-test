# Hadoop 에코시스템 실습 가이드

> Cloudera 클러스터 환경에서 HDFS / Hive / Spark / YARN 이 어떻게 함께 동작하는지 정리한 실습 노트

---

## 목차

1. [전체 아키텍처](#1-전체-아키텍처)
2. [HDFS](#2-hdfs)
3. [Parquet](#3-parquet)
4. [Hive](#4-hive)
5. [Spark](#5-spark)
6. [YARN](#6-yarn)
7. [MySQL vs Hive/HDFS 비교](#7-mysql-vs-hivehive-비교)
8. [역할 분리](#8-역할-분리)
9. [이 프로젝트 데이터 흐름](#9-이-프로젝트-데이터-흐름)

---

## 1. 전체 아키텍처

```
[개발자]
    ↓ spark-submit / SQL
[Spark / Hive / Impala]   ← 처리 엔진 (SQL 문법 동일)
    ↓
[YARN]                     ← 자원 관리자 (Worker 배분)
    ↓
[HDFS]                     ← 분산 파일 저장소
    ├── hdw1 (10.0.1.174)
    ├── hdw2 (10.0.1.175)
    └── hdw3 (10.0.1.176)
```

### 각 레이어 역할 한 줄 요약

```
처리 엔진  →  "어떻게 계산할지" 담당
YARN       →  "어느 서버의 자원을 얼마나 줄지" 담당
HDFS       →  "데이터가 실제로 어디 저장되어 있는지" 담당
```

### MySQL과 구조 비교

```
MySQL
└── 저장 + 처리 + 자원관리 전부 MySQL 혼자 담당 (서버 1대 기준)

Hadoop 에코시스템
├── 저장   →  HDFS
├── 처리   →  Spark / Hive / Impala
└── 자원   →  YARN
→ 역할이 분리된 이유: 서버 수백 대를 각각 전문화해서 운영
```

---

## 2. HDFS

### 개념

- 분산 파일 시스템 — 여러 서버에 파일을 나눠서 저장
- MySQL처럼 DB 엔진이 아니라 **파일 저장소**
- 파일을 **128MB 단위 Block**으로 쪼개서 여러 서버에 분산 저장
- 기본 복제본 **3개** (서버 1대 죽어도 데이터 유지)

```
1GB parquet 파일
├── Block 1 (128MB) → hdw1, hdw2, hdw3에 복제
├── Block 2 (128MB) → hdw2, hdw3, hdw1에 복제
├── ...
→ 사용자 눈에는 파일 1개, 실제론 24개 블록이 분산되어 있음
```

### 노드 역할

| 노드 | 역할 |
|:---|:---|
| **NameNode** | 파일 메타데이터 관리 (어느 블록이 어디 있는지 지도) |
| **DataNode** | 실제 데이터 블록 저장 (hdw1~hdw3) |
| **Secondary NameNode** | NameNode 메타데이터 백업 |

### 주요 경로 (이 환경)

```
/user/root/traffic_demo/input/         ← 원본 데이터 (개발자가 직접 올림)
/warehouse/tablespace/managed/hive/    ← Hive Managed Table 저장소
/tmp/                                  ← 임시 파일
/jars/                                 ← 공용 jar 파일
```

### Worker 목록 확인

```bash
sudo -u hdfs hdfs dfsadmin -report | grep -i "live datanodes\|^Name:"
```

### HDFS 경로 탐색

```bash
# 최상위 경로 탐색
hdfs dfs -ls /

# 프로젝트 경로 재귀 탐색
hdfs dfs -ls -R /user/root/traffic_demo

# 용량 확인
hdfs dfs -du -h /user/root/

# 파일 업로드 (로컬 → HDFS)
hdfs dfs -put -f /tmp/data.parquet /user/root/traffic_demo/input/

# 파일 다운로드 (HDFS → 로컬)
hdfs dfs -get /user/root/traffic_demo/input/file.parquet /tmp/
```

---

## 3. Parquet

### 개념

- 컬럼 기반 파일 포맷 (CSV, Excel 같은 파일 형식)
- Spark, Hive, Impala 등 여러 엔진이 공통으로 읽을 수 있음
- 압축 효율이 좋아서 Hadoop 생태계 표준 포맷
- **파일 자체에 스키마(컬럼명/타입) 내장** → CSV와 달리 별도 정의 불필요
- 폴더 경로로 읽으면 하위 parquet 파일 전부 자동으로 읽힘

### CSV vs Parquet 비교

```
CSV
├── 행(Row) 단위로 저장
├── 스키마 없음 (직접 지정해야 함)
└── 압축률 낮음

Parquet
├── 컬럼(Column) 단위로 저장
│   → 특정 컬럼만 읽을 때 해당 컬럼 블록만 I/O → 빠름
├── 스키마 내장 (footer에 포함)
└── Snappy, Gzip 등 압축 지원
```

### Spark에서 읽기

```python
# 폴더 경로 지정 → 하위 .parquet 파일 전부 읽힘
df = spark.read.parquet("/user/root/traffic_demo/input/traffic_volume_bronze")

# 스키마 확인
df.printSchema()

# snappy 압축 파일도 동일하게 읽음
df = spark.read.parquet("traffic_demo/input/traffic_volume_bronze/traffic_volume_bronze.snappy.parquet")
```

### Parquet 저장

```python
# 기본 저장
df.write.parquet("/user/root/traffic_demo/output/")

# 압축 지정
df.write.option("compression", "snappy").parquet("/user/root/output/")

# 모드 지정
df.write.mode("overwrite").parquet("/path/")   # 덮어쓰기
df.write.mode("append").parquet("/path/")      # 추가
```

---

## 4. Hive

### 개념

```
HDFS(데이터)  +  Hive Metastore(메타데이터)  =  테이블
```

- **Metastore** = "테이블 이름 ↔ HDFS 경로" 매핑 정보
- 데이터는 HDFS에, 메타(컬럼명/경로/포맷)는 Metastore에 따로 저장
- SQL로 조회 가능하지만 느림 → 배치 처리용
- Metastore 자체는 **MySQL 또는 PostgreSQL**에 저장됨

```
사용자 입장    →  테이블처럼 보임
실제 구조
├── Hive Metastore (MySQL) → "traffic_volume_bronze = /warehouse/.../traffic_volume_bronze/"
└── HDFS → /warehouse/.../traffic_volume_bronze/part-00000.parquet
```

### Managed Table vs External Table

| | Managed | External |
|:---|:---:|:---:|
| 저장 위치 | warehouse 자동 결정 | 경로 직접 지정 |
| DROP TABLE 시 | HDFS 파일도 삭제 | HDFS 파일 유지 |
| 실무 | 적게 사용 | 많이 사용 |

```sql
-- Managed Table (DROP 하면 데이터도 사라짐)
CREATE TABLE traffic_demo.traffic_volume_bronze (
    ...
) STORED AS PARQUET;

-- External Table (DROP 해도 파일 유지)
CREATE EXTERNAL TABLE traffic_demo.traffic_volume_bronze (
    ...
)
STORED AS PARQUET
LOCATION '/user/root/traffic_demo/input/traffic_volume_bronze/';
```

### Warehouse 경로 확인

```
Cloudera Manager → Hive Metastore → 설정 → warehouse 검색
→ hive.metastore.warehouse.dir

이 환경: /warehouse/tablespace/managed/hive/
```

### DB/테이블 구조

```
/warehouse/tablespace/managed/hive/
└── traffic_demo.db/              ← CREATE DATABASE로 자동 생성
    ├── traffic_volume_bronze/    ← 테이블 = 폴더
    │   └── part-00000.parquet    ← 실제 데이터
    └── traffic_volume_silver/
        └── part-00000.parquet
```

### 자주 쓰는 Hive SQL

```sql
-- DB 목록
SHOW DATABASES;

-- 테이블 목록
SHOW TABLES IN traffic_demo;

-- 테이블 구조 확인
DESCRIBE traffic_demo.traffic_volume_bronze;
DESCRIBE FORMATTED traffic_demo.traffic_volume_bronze;  -- 상세 (경로 포함)

-- 데이터 조회
SELECT * FROM traffic_demo.traffic_volume_bronze LIMIT 10;
```

---

## 5. Spark

### 개념

- 분산 처리 엔진 — HDFS 데이터를 Worker 여러 대에 나눠서 동시 처리
- Hive(느림/배치)보다 빠름
- `enableHiveSupport()` 로 Hive Metastore 연동 가능
- 언어: PySpark(Python), Scala, Java, R

### 실행 구조

```
Driver (지휘자, adm1 서버)
├── Worker1 (Executor) → hdw1에서 Block 처리
├── Worker2 (Executor) → hdw2에서 Block 처리
└── Worker3 (Executor) → hdw3에서 Block 처리
         ↓
    결과 합치기 → Driver로 반환
```

### Lazy Evaluation

```python
# Transformation (즉시 실행 안 됨)
df = df.filter(df.volume > 100)
df = df.select("timestamp", "volume")

# Action (이때 비로소 실제 실행)
df.show()
df.count()
df.write.parquet("/path/")
```

### spark-submit

```bash
spark-submit \
    --master yarn \          # YARN이 Worker 자원 관리
    --deploy-mode client \   # Driver를 현재 서버(adm1)에서 실행
    --name job_name \
    /tmp/script.py
```

```
deploy-mode 차이
client   →  Driver가 spark-submit 실행한 서버에서 돌아감 (로그 바로 보임)
cluster  →  Driver가 YARN Worker 중 하나에서 돌아감 (로그 YARN에서 확인)
```

### PySpark 기본 패턴

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("traffic_demo") \
    .enableHiveSupport() \        # Hive Metastore 연동
    .getOrCreate()

# HDFS에서 읽기
df = spark.read.parquet("/user/root/traffic_demo/input/traffic_volume_bronze")

# Hive 테이블에서 읽기
df = spark.sql("SELECT * FROM traffic_demo.traffic_volume_bronze")

# 가공
df_filtered = df.filter(df["volume"] > 100)

# Hive Managed Table로 저장
# 경로는 hive.metastore.warehouse.dir 기준으로 자동 결정
df_filtered.write \
    .mode("append") \
    .format("parquet") \
    .saveAsTable("traffic_demo.traffic_volume_silver")

# HDFS 경로에 직접 저장
df_filtered.write \
    .mode("overwrite") \
    .parquet("/user/root/traffic_demo/output/")

spark.stop()
```

### 자주 쓰는 DataFrame 연산

```python
# 스키마 확인
df.printSchema()
df.dtypes

# 데이터 미리보기
df.show(10)
df.show(10, truncate=False)   # 컬럼 내용 잘리지 않게

# 행 수
df.count()

# 컬럼 선택
df.select("col1", "col2")

# 필터
df.filter(df["volume"] > 100)
df.where("volume > 100")

# 컬럼 추가/변환
from pyspark.sql.functions import col, to_timestamp
df.withColumn("ts", to_timestamp(col("timestamp")))

# 집계
df.groupBy("location").agg({"volume": "sum"})

# 정렬
df.orderBy("timestamp")
df.orderBy(col("volume").desc())
```

---

## 6. YARN

### 개념

- 자원 관리자 — CPU/메모리를 Worker에게 배분
- `--master yarn` 한 줄로 분산처리 자동 설정
- **Queue**로 여러 작업의 자원을 분리 관리

### 구성 요소

| 컴포넌트 | 역할 |
|:---|:---|
| **ResourceManager** | 클러스터 전체 자원 관리 |
| **NodeManager** | 각 Worker 노드의 자원 관리 |
| **ApplicationMaster** | 개별 Job의 실행 조율 |

### Queue

```
YARN Queue Manager (Cloudera Manager에서 설정)
├── default queue  ← queue 미지정 시 여기로
├── 팀A queue      ← 자원 30% 할당
└── 팀B queue      ← 자원 20% 할당
```

```bash
# queue 지정
spark-submit --master yarn --queue 큐이름 ...

# queue 미지정 → default queue
spark-submit --master yarn ...
```

### YARN 상태 확인

```bash
# 노드 목록 및 상태
yarn node -list

# 실행 중인 애플리케이션
yarn application -list

# 특정 앱 로그
yarn logs -applicationId application_xxxxx
```

---

## 7. MySQL vs Hive/HDFS 비교

| | MySQL | Hive + HDFS |
|:---|:---|:---|
| 데이터 저장 | 서버 1대 디스크 | 여러 서버 분산 |
| 파일 포맷 | MySQL 전용 | Parquet (범용) |
| SQL 문법 | 표준 SQL | 표준 SQL (거의 동일) |
| 규모 | GB 단위 | TB ~ PB 단위 |
| 처리 엔진 | MySQL만 | Hive, Spark, Impala 모두 |
| 테이블 실체 | 진짜 테이블 존재 | 파일에 붙인 이름 (파일이 실체) |
| DROP TABLE | 데이터 삭제 | External이면 파일 유지 |
| UPDATE/DELETE | 자유롭게 가능 | 제한적 (파일 교체 방식) |
| 동시 접속 | OLTP에 최적화 | 배치/분석에 최적화 |

### 핵심 차이

```
MySQL  →  저장 + 처리가 한 몸 (서버 1대 최적화)
HDFS   →  저장과 처리가 분리
           같은 HDFS 데이터를 Impala도, Spark도, Hive도 읽을 수 있음
```

---

## 8. 역할 분리

| 클러스터 관리자 | 데이터 엔지니어 |
|:---|:---|
| Cloudera Manager 설치/설정 | HDFS 경로 설계 |
| YARN Queue 생성/배분 | Spark / Hive 코드 작성 |
| 노드 추가/장애 대응 | Oozie workflow 구성 |
| 보안(Ranger) 설정 | 이미 만들어진 Queue 사용 |
| DataNode 디스크 관리 | 데이터 파이프라인 운영 |

```
데이터 엔지니어가 신경 쓰는 것
→ "어느 HDFS 경로에 저장할지"
→ "spark-submit 옵션 어떻게 줄지"
→ "Hive 테이블 스키마 어떻게 설계할지"

클러스터 관리자가 이미 해준 것
→ YARN이 동작하는 환경
→ HDFS가 동작하는 환경
→ Spark이 설치된 환경
```

---

## 9. 이 프로젝트 데이터 흐름

```
[로컬 parquet 파일]
    ↓ 10_upload.sh
[HDFS] /user/root/traffic_demo/input/traffic_volume_bronze/
    ↓ 22_create_table_spark.sh
    Spark: HDFS 원본 읽기 → 컬럼명 부여 → Hive 테이블로 저장
[Hive Table] traffic_demo.traffic_volume_bronze
    ↓ 32_bronze_to_silver_spark.sh
    Spark: bronze 테이블 읽기 → 가공 (필터/집계) → silver 테이블로 저장
[Hive Table] traffic_demo.traffic_volume_silver
    ↓ 50_save_result.sh
[HDFS] /user/root/traffic_demo/output/count_result.txt
```

### 스크립트별 역할

| 스크립트 | 역할 | 사용 기술 |
|:---|:---|:---|
| `10_upload.sh` | 로컬 → HDFS 업로드 | `hdfs dfs -put` |
| `22_create_table_spark.sh` | 원본 parquet → Hive bronze 테이블 생성 | PySpark + saveAsTable |
| `32_bronze_to_silver_spark.sh` | bronze → 가공 → silver 테이블 | PySpark |
| `50_save_result.sh` | 결과를 텍스트로 저장 | PySpark |

### Bronze / Silver / Gold 패턴 (Medallion Architecture)

```
Bronze  →  원본 그대로 저장 (raw data)
Silver  →  정제/가공된 데이터 (cleaned data)
Gold    →  집계/분석용 데이터 (aggregated data)

→ 실무에서 Hadoop 데이터 파이프라인 표준 패턴
```
