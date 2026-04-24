# CDE - Cloudera Data Engineering (Claude 정리)

> GPT 답변 + Gemini 답변을 종합 정리한 버전

## CDE란?

**Apache Spark를 기반으로 하는 서버리스 데이터 엔지니어링 서비스**입니다.

데이터를 추출(Extract), 변환(Transform), 저장(Load)하는 **ETL 파이프라인**을 구축하고 실행하는 플랫폼입니다.

## Cloudera에서의 역할

Gemini 관점 (CDP 서비스 수준):
- Kubernetes를 활용한 자동 자원 할당 (서버리스)
- Apache Airflow 통합으로 복잡한 작업 스케줄링
- Apache Spark 기반 데이터 변환 작업

GPT 관점 (컴포넌트 수준):
- **Oozie**: 스케줄링/오케스트레이션 담당 (→ CDE에서 Airflow로 현대화)
- **Spark**: 실제 데이터 처리 실행 엔진

## Databricks 대응

| CDE 기능 | Databricks 대응 |
|:---|:---|
| Airflow 워크플로 스케줄링 | **Lakeflow Jobs (Databricks Workflows)** |
| Spark ETL 실행 | **Databricks Compute (Spark)** |
| 선언형 파이프라인 | **Delta Live Tables (DLT)** |
| 서버리스 실행 환경 | **Serverless Compute** |
| Kubernetes 기반 자원 관리 | **플랫폼이 내부 처리** |

### Databricks의 추가 강점
Gemini가 강조했듯이, **Delta Live Tables(DLT)** 는 CDE에 없는 Databricks만의 강점입니다.
- CDE: "어떻게 처리할지"를 코드로 직접 작성 (명령형)
- DLT: "무엇을 원하는지"만 SQL/Python으로 정의하면 실행·모니터링·재처리 자동화 (선언형)

## 한 줄 요약

**CDE ≈ Lakeflow Jobs + Spark Compute + Delta Live Tables**
(Databricks가 선언형 파이프라인에서 추가 강점 보유)
