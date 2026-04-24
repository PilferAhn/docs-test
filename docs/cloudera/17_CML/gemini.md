# CML - Cloudera Machine Learning (Gemini 답변)

> 출처: Gemini 답변 원문

## 3. 머신러닝 & AI

모델 학습, 배포 및 관리(MLOps)를 위한 환경입니다.

### Cloudera Machine Learning (CML)
Cloudera Data Science Workbench(CDSW)의 진화형입니다.
- Jupyter, RStudio 등 익숙한 IDE를 컨테이너 환경에서 제공
- 모델 배포 및 모니터링 기능을 포함
- 최근에는 **LLM을 위한 AI Studio 기능**이 강화됨

### Databricks 대응: Mosaic AI (이전 Databricks ML)
MLflow라는 업계 표준 오픈소스를 만든 곳답게 실험 추적 및 모델 관리가 매우 강력합니다.

- **통합 노트북 환경**에서 데이터 준비부터 배포까지 원스톱으로 이루어짐
- **MLflow**: 실험 추적, 모델 버전 관리 업계 표준
- **MosaicML 인수**를 통해 생성형 AI(GenAI) 학습 분야에서 압도적 우위

### 주요 차이점
| 항목 | CML | Mosaic AI (Databricks ML) |
|:---|:---|:---|
| IDE 지원 | Jupyter, RStudio (컨테이너 기반) | 통합 Notebook |
| 실험 추적 | 기본 제공 | MLflow (업계 표준 오픈소스) |
| 모델 배포 | 지원 | Model Serving (더 고도화) |
| GenAI 지원 | AI Studio (강화 중) | MosaicML 기반 (압도적 우위) |
| MLOps 생태계 | 제한적 | 매우 강력 |
