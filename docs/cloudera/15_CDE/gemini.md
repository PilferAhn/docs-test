# CDE - Cloudera Data Engineering (Gemini 답변)

> 출처: Gemini 답변 원문

## 1. 데이터 엔지니어링 (ETL & Pipeline)

데이터를 추출, 변환, 로드(ETL)하여 파이프라인을 구축하는 단계입니다.

### Cloudera Data Engineering (CDE)
Apache Spark를 기반으로 하는 서버리스 데이터 엔지니어링 서비스입니다.
- Kubernetes를 활용하여 리소스를 자동 할당
- **Airflow와 통합**되어 복잡한 작업 스케줄링을 지원
- 서버리스 방식으로 인프라 관리 부담을 줄임

### Databricks 대응: Databricks Workflows (Jobs)
Databricks의 핵심 기능으로, Spark 작업을 스케줄링하고 DAG(Directed Acyclic Graph) 형태로 파이프라인을 관리합니다.

- CDE보다 서버리스 환경이 더 고도화됨
- **Delta Live Tables(DLT)**: 선언형 ETL을 지원하는 것이 특징
  - 선언형: "무엇을 원하는지"만 정의하면 시스템이 알아서 실행

### 주요 차이점
| 항목 | CDE (Airflow 기반) | Databricks Workflows |
|:---|:---|:---|
| 스케줄러 | Apache Airflow | 내장 스케줄러 |
| ETL 방식 | 명령형 (어떻게 처리할지 직접 코딩) | 선언형 지원 (Delta Live Tables) |
| 서버리스 | 지원 (Kubernetes 기반) | 더 고도화된 서버리스 |
| 실행 엔진 | Apache Spark | Apache Spark + Photon |
