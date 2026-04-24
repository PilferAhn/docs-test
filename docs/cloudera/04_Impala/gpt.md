# Impala (GPT 답변)

> 출처: ChatGPT 답변 원문

## Cloudera에서의 역할

Impala는 Cloudera의 대표적인 **저지연 MPP SQL 엔진**입니다.
**고성능, 저지연 SQL 쿼리**를 Hadoop 파일 포맷 데이터에 대해 실행합니다.
내부적으로는 분산 MPP 데이터베이스 엔진 구조를 가지며, `impalad` 데몬들이 병렬로 쿼리 조각을 실행합니다.

### 실제 역할 상세
- BI/대시보드/애드혹 쿼리
- Hive보다 빠른 대화형 SQL
- HDFS/Kudu 기반 데이터에 대한 고성능 분석
- JDBC/ODBC 연동에 적합

## Databricks 대응

가장 직접적인 대응은 **Databricks SQL warehouse**입니다.

Databricks SQL warehouse는 Databricks SQL에서 데이터 오브젝트에 대해 SQL 명령을 실행하는 compute 리소스입니다.
Databricks도 공식적으로 대부분의 경우 serverless SQL warehouse 사용을 권장합니다.

### 차이점
- Impala는 Hadoop 생태계 안의 별도 MPP 엔진
- Databricks SQL warehouse는 Databricks 플랫폼 안의 SQL 전용 compute
- Databricks에서는 메타스토어/권한/실행/UI가 Impala보다 더 통합적으로 묶임

## 한 줄 매핑

**Impala ≈ Databricks SQL warehouse**
이건 비교적 1:1에 가장 가깝습니다.
