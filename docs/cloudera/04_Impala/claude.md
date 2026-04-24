# Impala (Claude 정리)

> GPT 답변 + Gemini 답변을 종합 정리한 버전

## Impala란?

Cloudera의 **저지연(Low-latency) 고성능 SQL 엔진**입니다.

"MPP(Massively Parallel Processing)" 방식으로 여러 서버가 동시에 쿼리를 나눠 처리해서 빠른 응답을 냅니다.
내부적으로 `impalad` 데몬들이 병렬로 쿼리 조각을 실행합니다.

## Cloudera에서의 역할

GPT와 Gemini 모두 동일하게 설명합니다.

- BI 도구(Tableau, Power BI 등)와 연결해 대시보드 실시간 조회
- 즉시 결과가 필요한 애드혹(Ad-hoc) 쿼리
- HDFS나 Kudu 기반 데이터의 고성능 분석
- JDBC/ODBC 연동에 적합
- **Hive보다 대화형 응답이 훨씬 빠른 것이 강점**

## Databricks 대응

GPT와 Gemini 모두 **Databricks SQL Warehouse**를 직접 대응으로 지목합니다.
이는 전체 서비스 중 **1:1 대응에 가장 가까운 경우**입니다.

| 항목 | Impala | Databricks SQL Warehouse |
|:---|:---|:---|
| 목적 | 저지연 대화형 SQL | 저지연 대화형 SQL |
| 실행 엔진 | 자체 MPP 엔진 | Photon (C++ 기반, Spark 위) |
| 배포 | HDFS 위, 별도 데몬 | 클라우드 오브젝트 스토리지, Serverless 지원 |
| 권한 관리 | 별도 Ranger 연동 필요 | Unity Catalog 내장 |
| BI 연결 | JDBC/ODBC | JDBC/ODBC + Partner Connect |

## 한 줄 요약

**Impala ≈ Databricks SQL Warehouse**
(이 대응이 전체 서비스 중 가장 직접적입니다)
