# Oozie (Claude 정리)

> GPT 답변 + Gemini 답변을 종합 정리한 버전

## Oozie란?

**여러 작업을 순서대로 조율하고 스케줄링하는 워크플로 관리 서비스**입니다.

공정 자동화 지휘자에 비유할 수 있습니다.
"먼저 A 작업, 완료되면 B와 C 동시 실행, 둘 다 끝나면 D 실행" 같은 흐름을 정의하고 자동 실행합니다.

> **DAG란?** Directed Acyclic Graph. 작업들의 순서 흐름도로, 사이클(무한 반복)이 없는 방향 그래프입니다.

## Cloudera에서의 역할

GPT와 Gemini 모두 동일하게 설명합니다.

- 시간 기반 스케줄링 (매일 오전 2시 실행 등)
- 파일 도착/데이터 준비 상태 기반 트리거
- Hive, Spark, MapReduce 등 여러 작업의 DAG 관리
- 실패 시 재시도, 선후행 의존성 제어

Gemini 추가 관점: Cloudera 생태계 내에서도 Oozie → Airflow 전환 흐름이 있으며,
CDE(Cloudera Data Engineering)는 Airflow를 통합해 더 현대적인 형태로 발전했습니다.

## Databricks 대응

GPT: **Lakeflow Jobs** (명확한 1:1 대응)
Gemini: **Databricks Workflows (Jobs) + Delta Live Tables** (CDE 전체 기준)

두 관점 모두 **Lakeflow Jobs / Databricks Workflows**가 핵심 대응임을 가리킵니다.

| 기능 | Oozie | Lakeflow Jobs |
|:---|:---|:---|
| 스케줄링 | 시간·데이터 기반 | 시간·파일 도착·이벤트 기반 |
| 파이프라인 정의 | XML 기반 | UI / YAML / Python |
| 선언형 ETL | ❌ | ✅ (Delta Live Tables) |
| 서버리스 | ❌ | ✅ |
| 모니터링 UI | 기본 수준 | 시각적 DAG UI |

## 한 줄 요약

**Oozie ≈ Lakeflow Jobs (Databricks Workflows)**
(전체 서비스 중 1:1 대응에 가장 가까운 경우 중 하나)
