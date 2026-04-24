# Cloudera vs Databricks 전체 매핑 (Gemini 답변)

> 출처: Gemini 답변 원문 정리

## 두 플랫폼의 뿌리

Cloudera와 Databricks는 모두 데이터 관리와 분석을 위한 거대 플랫폼이지만, 그 뿌리가 다릅니다.

- **Cloudera**: 전통적인 Hadoop 기반의 하이브리드 클라우드에 강점
- **Databricks**: Apache Spark 기반의 클라우드 네이티브 Lakehouse 모델을 선도

## 서비스 매핑 요약표

| 구분 | Cloudera (CDP) | Databricks (Lakehouse) | 주요 차이점 |
|:---|:---|:---|:---|
| **핵심 엔진** | Hive, Impala, Spark, NiFi | Apache Spark, Photon 엔진 | Cloudera는 도구의 다양성, Databricks는 엔진의 통일성 |
| **데이터 엔지니어링** | CDE (Airflow 기반) | Workflows / Delta Live Tables | Databricks가 선언형 파이프라인에 더 강점 |
| **웨어하우스/BI** | CDW (Impala/Hive) | Databricks SQL | CDW는 전통적 SQL 강세, DB SQL은 속도와 서버리스 강조 |
| **머신러닝/AI** | CML | Mosaic AI (MLflow 기반) | Databricks가 GenAI 및 MLOps 생태계에서 우위 |
| **실시간 처리** | CDF (NiFi/Flink/Kafka) | Spark Structured Streaming | Cloudera는 수집과 복잡한 스트리밍 로직에 강점 |
| **거버넌스** | SDX (Ranger/Atlas) | Unity Catalog | SDX는 하이브리드 환경, Unity는 클라우드 네이티브에 최적 |

## 최종 요약

- **Cloudera**: 기존 Hadoop 환경을 쓰거나, 보안/규제가 엄격한 온프레미스와 클라우드를 병행해야 하는 대기업에 유리
- **Databricks**: 클라우드 환경에서 AI와 머신러닝을 핵심 가치로 두며, 데이터 엔지니어링과 분석을 하나의 플랫폼(Lakehouse)으로 단순화하려는 조직에 더 적합
