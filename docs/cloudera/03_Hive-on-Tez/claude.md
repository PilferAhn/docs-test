# Hive on Tez (Claude 정리)

> GPT 답변 + Gemini 답변을 종합 정리한 버전

## Hive on Tez란?

사용자가 SQL을 입력하면 그것을 받아서 실제로 실행해 주는 **SQL 쿼리 엔진**입니다.

구조를 풀어보면:
- **HiveServer2**: SQL을 받는 서버 (JDBC/ODBC/Beeline/Hue 등으로 연결)
- **Hive**: SQL을 파싱하고 실행 계획을 만드는 부분
- **Tez**: Hive가 만든 실행 계획을 실제로 분산 실행하는 엔진

## Cloudera에서의 역할

주로 **배치성 SQL, ETL, 대용량 데이터 변환 작업**에 사용됩니다.

- Impala보다 대화형 응답은 다소 느리지만, 복잡한 SQL이나 ETL에서는 강점
- Hive LLAP(Live Long And Process): Tez 위에 메모리 캐싱을 추가한 발전형 → CDW에서 사용

## Databricks 대응

GPT와 Gemini가 약간 다른 각도로 설명합니다.

**GPT 관점** — 용도에 따라 분리:
- ETL/배치 SQL → **Databricks Compute (Spark)**
- 즉시 SQL 조회 → **SQL Warehouse**

**Gemini 관점** — CDW 전체로 비교:
- Cloudera CDW(Hive+Impala) ↔ **Databricks SQL**
- Photon 엔진(C++ 기반)이 Tez보다 더 빠른 성능 제공

### 두 관점 종합

| 사용 목적 | Cloudera | Databricks |
|:---|:---|:---|
| 복잡한 ETL, 대용량 변환 | Hive on Tez | Databricks Compute (Spark) |
| BI 즉시 조회, 대화형 SQL | Impala 또는 Hive LLAP | SQL Warehouse (Photon) |
| 서버리스 SQL 실행 | CDW Virtual Warehouse | Serverless SQL Warehouse |

## 한 줄 요약

**Hive on Tez ≈ SQL Warehouse(즉시 조회) + Spark Compute(ETL 배치)**
