# Tez (GPT 답변)

> 출처: ChatGPT 답변 원문

## Cloudera에서의 역할

Tez는 Hive 실행 엔진 쪽 핵심입니다.
**vertex와 task로 이루어진 그래프를 실행하는 프레임워크**이며, Hive 쿼리의 물리 실행 계획이 이 위에서 만들어집니다.
사용자가 직접 SQL을 치면 보이는 건 Hive지만, 실제 분산 실행 DAG를 굴리는 건 Tez입니다.

### 실제 역할 상세
- Hive 쿼리를 DAG로 실행
- MapReduce보다 더 유연하고 효율적인 실행 모델
- 실행 엔진 자체이므로 사용자가 직접 "Tez SQL"을 쓰는 것은 아님

## Databricks 대응

Tez는 Databricks에서 별도 제품으로 보이지 않습니다.
그 역할은 **Spark execution engine** 안으로 흡수되어 있습니다.

- Hive on Tez에서 Tez가 맡던 분산 DAG 실행 역할
- Databricks에서는 **Spark engine이 내부적으로 수행**

사용자 관점에서는 notebook/job/SQL warehouse를 쓰지, "Tez에 해당하는 독립 서비스"를 관리하지 않습니다.

## 한 줄 매핑

**Tez ≈ Databricks 내부 Spark execution layer**
독립 서비스 대응 없음
