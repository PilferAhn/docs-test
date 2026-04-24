# CDE - Cloudera Data Engineering (GPT 답변)

> 출처: ChatGPT 답변 원문
> GPT는 CDE를 직접 다루지 않고, CDE 내 개별 컴포넌트(Oozie, Spark 등)를 중심으로 설명했습니다.

## GPT가 다룬 관련 컴포넌트

CDE는 다음 하둡 컴포넌트들을 CDP 상위 서비스로 묶은 것입니다.

### Oozie → Lakeflow Jobs
- Oozie: 작업 간 의존성 오케스트레이션, 시간/데이터 기반 스케줄링
- 대응: **Lakeflow Jobs** (가장 직접적인 1:1 대응)
- 상세 내용: `06_Oozie/gpt.md` 참고

### Spark (실행 엔진)
- CDE는 Apache Spark 기반 서버리스 데이터 엔지니어링 서비스
- Spark 작업 실행은 Databricks Compute(Spark)로 직접 대응

## GPT 관점 요약

CDE는 GPT 답변에서 직접 비교되지 않았으나,
CDE를 구성하는 핵심 컴포넌트(Oozie → Jobs, Spark → Compute)는 명확하게 대응됩니다.

- **스케줄링/오케스트레이션**: Oozie → **Lakeflow Jobs**
- **실행 엔진**: Spark → **Databricks Compute**
- **선언형 ETL**: 없음 → **Delta Live Tables** (Databricks 추가 강점)
