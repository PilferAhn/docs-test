# Hive on Tez (GPT 답변)

> 출처: ChatGPT 답변 원문

## Cloudera에서의 역할

**Hive on Tez가 Apache Hive SQL 데이터베이스를 Apache Tez 위에서 실행하는 서비스**입니다.
Hive가 단순 메타데이터 서비스가 아니라, HiveServer2를 통해 SQL을 받아 실제 분산 실행 계획을 돌리는 쿼리 엔진입니다.

HMS(Hive Metastore)는 별도 서비스로 분리되어 있습니다.

### 실제 역할 상세
- 사용자가 JDBC/ODBC/Beeline/Hue로 SQL을 던지면 HiveServer2가 받음
- 쿼리를 파싱/최적화한 뒤, Tez DAG로 변환해 실행
- 배치성 SQL, ETL, 대용량 변환 작업에 자주 사용
- 전통적으로 Impala보다 대화형 응답성은 느릴 수 있지만, 복잡한 SQL/ETL에는 강점

## Databricks 대응

용도에 따라 둘로 나뉩니다.

1. **ETL/배치 SQL 엔진 관점**
   → Databricks compute(Spark) 위에서 돌아가는 SQL/DataFrame 작업

2. **사용자 SQL 엔드포인트 관점**
   → Databricks SQL warehouse 또는 notebook/job compute

Databricks의 SQL warehouse는 SQL 명령을 실행하는 compute 리소스이고,
Databricks compute는 노트북/잡/자동화 워크로드용 일반 실행 엔진입니다.

## 한 줄 매핑

**Hive on Tez ≈ Databricks SQL warehouse + Databricks Spark compute**
- ETL이면 compute, BI성 SQL이면 SQL warehouse가 더 가깝습니다.
