# CML - Cloudera Machine Learning (Claude 정리)

> GPT 답변 + Gemini 답변을 종합 정리한 버전
> (이 서비스는 Gemini 답변이 주된 출처입니다. GPT는 하둡 컴포넌트 수준에서 비교했기 때문에 CML을 직접 다루지 않았습니다.)

## CML이란?

**머신러닝 모델을 개발, 학습, 배포, 모니터링하는 통합 플랫폼**입니다.

데이터 과학자가 쓰던 Jupyter Notebook, RStudio 같은 도구를 **컨테이너 환경에서 클라우드로 제공**하는 서비스입니다.

## Cloudera에서의 역할

CML은 Cloudera Data Science Workbench(CDSW)의 진화형입니다.

주요 기능:
- Jupyter, RStudio 등 익숙한 IDE를 컨테이너(Docker) 환경에서 제공
- 모델 학습, 배포, 모니터링 통합
- 최근 AI Studio 기능으로 LLM(대형 언어 모델) 지원 강화

## Databricks 대응

Gemini는 **Mosaic AI (이전 Databricks ML)** 를 대응으로 지목합니다.

| 항목 | CML | Mosaic AI |
|:---|:---|:---|
| 개발 환경 | Jupyter/RStudio (컨테이너) | 통합 Databricks Notebook |
| 실험 추적 | 기본 제공 | **MLflow** (업계 표준, Databricks가 만든 오픈소스) |
| 모델 관리 | 지원 | Unity Catalog의 Model Registry |
| 모델 배포 | 지원 | **Model Serving** (더 고도화) |
| GenAI/LLM | AI Studio (강화 중) | **MosaicML 기반** (압도적 우위) |
| MLOps 생태계 | 자체 생태계 | MLflow 중심의 넓은 생태계 |

### Databricks의 주요 강점
1. **MLflow**: 실험 추적 업계 표준 — Databricks가 직접 만든 오픈소스
2. **MosaicML 인수**: 대규모 LLM(생성형 AI) 모델 학습 분야에서 선도
3. **통합 환경**: 데이터 준비 → 모델 학습 → 배포까지 단일 플랫폼

## 한 줄 요약

**CML ≈ Mosaic AI (MLflow + Model Serving + GenAI 지원)**
(특히 GenAI/MLOps 생태계에서 Databricks가 우위)
