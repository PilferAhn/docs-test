# Tez (Claude 정리)

> GPT 답변 + Gemini 답변을 종합 정리한 버전

## Tez란?

**Hive 쿼리를 실제로 분산 실행하는 내부 실행 엔진**입니다.

사용자는 "Tez를 쓴다"고 의식하지 않지만, Hive가 SQL을 받아 처리할 때 내부에서 자동으로 사용됩니다.

흐름:
```
사용자 SQL 입력
  → HiveServer2 수신
  → Hive: SQL 파싱 + 실행 계획(DAG) 생성
  → Tez: DAG를 여러 서버에 분산 실행
  → 결과 반환
```

## Cloudera에서의 역할

GPT 관점:
- Hive 쿼리를 DAG(방향성 비순환 그래프)로 실행
- MapReduce보다 더 유연하고 효율적인 실행 모델
- 사용자가 직접 "Tez"를 조작하지 않음 (내부 엔진)

Gemini 관점 (CDW 맥락):
- Hive LLAP = Tez 위에 메모리 캐싱을 추가한 발전형
- CDW에서 더 빠른 쿼리 응답을 위해 사용

## Databricks 대응

GPT와 Gemini 모두 동일한 결론을 냅니다.
**Tez에 대응하는 별도 서비스가 없으며, Spark 실행 엔진 내부로 흡수**됩니다.

| 항목 | Tez | Databricks 내부 |
|:---|:---|:---|
| 역할 | Hive 쿼리 분산 실행 | Spark execution engine |
| Gemini 추가 | Hive LLAP의 기반 | Photon 엔진 (C++ 벡터화) |
| 사용자 노출 | 없음 (내부 엔진) | 없음 (내부 엔진) |
| 독립 서비스? | Cloudera에서는 별도 서비스로 표시됨 | Databricks에서는 완전히 숨겨짐 |

## 한 줄 요약

**Tez ≈ Databricks 내부 Spark 실행 레이어 (+ Photon 엔진)**
(독립 서비스 대응 없음, 플랫폼이 완전히 흡수)
