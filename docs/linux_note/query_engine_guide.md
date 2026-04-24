# Impala vs Hive vs Spark — 언제 뭘 써야 하나?

> Cloudera 실습 중 자주 헷갈리는 쿼리 엔진 3종 비교 정리

---

## 한 줄 요약

| 엔진 | 한 줄 요약 |
|:---|:---|
| **Impala** | 빠른 조회 — "지금 당장 결과 봐야 해" |
| **Hive** | 안정적인 대용량 처리 — "천천히 정확하게" |
| **Spark** | 복잡한 변환·ML — "코드로 데이터 다루고 싶어" |

---

## 1. Impala

### 특징
- **메모리 기반** 분산 SQL 엔진
- 쿼리를 받는 즉시 실행 → **응답 속도가 매우 빠름**
- MapReduce/Tez 없이 직접 HDFS/Kudu 데이터를 읽음

### 이럴 때 써라
- BI 대시보드, Hue에서 데이터 탐색할 때
- 결과를 **즉시** 확인하고 싶을 때 (초~수십 초 단위)
- `SELECT`, `JOIN`, `GROUP BY` 등 일반적인 SQL 조회
- 테이블 생성/메타데이터 관리 (`CREATE TABLE`, `DESCRIBE`)

### 이럴 때 쓰지 마라
- 수 시간짜리 대용량 배치 ETL
- 복잡한 윈도우 함수나 UDF가 많을 때
- 메모리 초과 가능성 있는 매우 큰 JOIN

```bash
# 사용 예시 (02_create_table.sh에서 한 것처럼)
impala-shell -i hdw1.ktwings.dd.io:21050 <<EOF
SELECT * FROM traffic_demo.traffic_volume LIMIT 10;
EOF
```

---

## 2. Hive

### 특징
- SQL을 **MapReduce 또는 Tez 잡**으로 변환해서 실행
- 속도는 느리지만 **안정성과 내결함성**이 뛰어남
- Hive Metastore = 테이블 스키마 정보를 저장하는 중앙 저장소
  - Impala, Spark 모두 Hive Metastore를 공유해서 씀

### 이럴 때 써라
- 대용량 ETL 배치 (수억 건 이상)
- 오래 걸려도 되는 야간 배치 작업
- Oozie 워크플로우에서 안정적으로 돌려야 할 때
- 복잡한 집계, 변환이 들어간 대규모 데이터 처리

### 이럴 때 쓰지 마라
- 빠른 조회가 필요할 때 → Impala 써라
- 실시간 또는 준실시간 처리 → Spark Streaming 써라

```bash
# 사용 예시
hive -e "SELECT COUNT(*) FROM traffic_demo.traffic_volume;"

# 또는 hive 쉘 접속
hive
> USE traffic_demo;
> SELECT * FROM traffic_volume LIMIT 10;
```

---

## 3. Spark

### 특징
- **인메모리 분산 처리** 프레임워크 (엔진이자 프레임워크)
- Python(PySpark), Scala, Java, R로 코드 작성 가능
- SQL뿐 아니라 **ML, 스트리밍, 복잡한 데이터 변환** 가능
- Hive Metastore 연동해서 테이블 읽고 쓰기 가능

### 이럴 때 써라
- 데이터 변환 로직이 SQL만으로는 표현하기 어려울 때
- ML 모델 학습/예측 파이프라인
- 실시간 스트리밍 처리 (Spark Streaming)
- Bronze → Silver → Gold 레이어 변환 ETL (Databricks 스타일)
- 복잡한 UDF, 커스텀 집계 로직

### 이럴 때 쓰지 마라
- 단순 SELECT 조회 → Impala가 훨씬 빠름
- 코드 없이 SQL만으로 충분한 작업 → Hive나 Impala 써라

```python
# PySpark 사용 예시
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("traffic_silver").getOrCreate()

df = spark.table("traffic_demo.traffic_volume")
df.show(10)

# Silver 변환
from pyspark.sql.functions import current_timestamp

silver_df = df.dropna().withColumn("_processed_at", current_timestamp())
silver_df.write.mode("overwrite").parquet("/user/root/traffic_demo/silver/")
```

---

## 4. 한눈에 비교

| 항목 | Impala | Hive | Spark |
|:---|:---:|:---:|:---:|
| 속도 | ⚡ 빠름 | 🐢 느림 | ⚡ 빠름 (메모리) |
| 안정성 (대용량) | 보통 | 높음 | 높음 |
| 인터페이스 | SQL | SQL | SQL + 코드 |
| 실시간 처리 | ❌ | ❌ | ✅ |
| ML 지원 | ❌ | ❌ | ✅ |
| 주 사용 목적 | 빠른 조회 | 배치 ETL | 복잡한 변환·ML |
| Oozie 연동 | ✅ | ✅ | ✅ |
| 메타스토어 | Hive Metastore | Hive Metastore | Hive Metastore |

---

## 5. Cloudera 실습 흐름에서의 역할

```
HDFS (원본 파일 저장)
    │
    ├─ Impala         → 빠른 탐색, 테이블 생성, 확인용 SELECT
    │
    ├─ Hive           → 대용량 배치 변환, Oozie 안정 배치
    │
    └─ Spark          → 복잡한 ETL, Silver/Gold 레이어 변환, ML
```

> **우리 실습 기준:**
> - 테이블 만들고 확인하는 건 → `impala-shell` (02_create_table.sh, 04_preview.sh)
> - 나중에 Silver 변환 배치 짜려면 → Spark 또는 Hive 고려
