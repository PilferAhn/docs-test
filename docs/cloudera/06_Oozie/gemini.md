# Oozie (Gemini 답변)

> 출처: Gemini 답변 원문
> Gemini는 Oozie를 CDE(Cloudera Data Engineering) 카테고리 안에서 간접적으로 다뤘습니다.

## CDE (Cloudera Data Engineering) — Oozie 포함

### Cloudera CDE 설명
Apache Spark를 기반으로 하는 서버리스 데이터 엔지니어링 서비스입니다.
- **Airflow와 통합**되어 복잡한 작업 스케줄링을 지원
- Kubernetes를 활용하여 리소스를 자동 할당

CDE에서 Airflow가 스케줄링 역할을 하며, 이는 Oozie의 후속/대체 역할에 해당합니다.

### Oozie → Airflow 전환 맥락
Cloudera 생태계 내에서도 Oozie에서 Airflow로의 전환 흐름이 있습니다.
CDE는 Airflow를 통합해 더 현대적인 워크플로 관리를 제공합니다.

### Databricks 대응: Databricks Workflows (Jobs)
- Spark 작업을 스케줄링하고 DAG(Directed Acyclic Graph) 형태로 파이프라인 관리
- **Delta Live Tables(DLT)**를 통해 선언형 ETL을 지원
- CDE보다 서버리스 환경이 더 고도화

### 주요 차이점
| 항목 | Oozie / CDE(Airflow) | Databricks Workflows |
|:---|:---|:---|
| 스케줄링 | 시간·데이터 기반 트리거 | 시간·파일 도착·이벤트 기반 트리거 |
| 파이프라인 정의 | XML(Oozie) / Python DAG(Airflow) | UI 또는 YAML/JSON |
| ETL 방식 | 명령형 | 선언형(DLT) 지원 |
