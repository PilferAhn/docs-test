# Hive Metastore (Gemini 답변)

> 출처: Gemini 답변 원문
> Gemini는 Hive Metastore를 개별 컴포넌트로 다루지 않고, CDW(데이터 웨어하우징) 카테고리 안에서 간접적으로 언급했습니다.

## Gemini의 관련 언급

### CDW(데이터 웨어하우징) 맥락에서
Cloudera Data Warehouse(CDW)는 Apache Hive(LLAP)와 Impala 엔진을 사용합니다.
이 엔진들은 Hive Metastore를 통해 테이블 정보를 공유합니다.

Databricks SQL은 이에 대응하며, Unity Catalog가 메타데이터 관리 역할을 담당합니다.

### 거버넌스(SDX) 맥락에서
- Cloudera SDX는 Apache Ranger와 Atlas를 기반으로 전사 데이터 거버넌스를 제공
- Databricks Unity Catalog는 메타데이터 + 권한 + 계보를 통합 관리

Hive Metastore의 메타데이터 역할은 Unity Catalog metastore로 이전됩니다.

## Gemini 관점 요약

Gemini 답변에서 Hive Metastore는 독립 서비스로 비교되지 않았습니다.
상세 비교는 GPT 답변(`gpt.md`) 또는 Claude 정리(`claude.md`)를 참고하세요.
