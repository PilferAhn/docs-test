# Tez (Gemini 답변)

> 출처: Gemini 답변 원문
> Gemini는 Tez를 개별 컴포넌트로 별도 다루지 않았습니다.
> Hive의 실행 엔진으로서 CDW 맥락에서 간접 언급됩니다.

## Gemini의 관련 언급

### CDW 맥락에서 (Hive 실행 엔진)
Cloudera Data Warehouse(CDW)는 Apache Hive(LLAP)를 사용합니다.
Hive LLAP는 Tez 위에 메모리 캐싱을 추가한 발전형입니다.

Databricks에서 이 실행 엔진 역할은 **Photon 엔진**이 담당합니다.
- Photon: C++ 기반의 고성능 벡터화(vectorized) 실행 엔진
- Spark 위에 올라가며 SQL 쿼리 성능을 극적으로 향상

### 비교
| 항목 | Tez / Hive LLAP | Databricks Photon |
|:---|:---|:---|
| 역할 | Hive 쿼리 분산 실행 | Spark SQL 벡터화 실행 |
| 언어 | Java 기반 | C++ 기반 |
| 사용자 노출 | 보이지 않음 (내부 엔진) | 보이지 않음 (내부 엔진) |

## Gemini 관점 요약

Tez는 Gemini 답변에서 독립 서비스로 비교되지 않았습니다.
상세 비교는 GPT 답변(`gpt.md`) 또는 Claude 정리(`claude.md`)를 참고하세요.
