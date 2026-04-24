# CDP-INFRA-SOLR (Gemini 답변)

> 출처: Gemini 답변 원문
> Gemini는 CDP-INFRA-SOLR을 개별 컴포넌트로 별도 다루지 않았습니다.
> SDX(거버넌스) 카테고리와 간접적으로 관련됩니다.

## Gemini의 관련 내용

### SDX (거버넌스) 맥락에서
Cloudera SDX는 Apache Ranger와 Atlas를 기반으로 합니다.
CDP-INFRA-SOLR은 Ranger의 감사 로그를 인덱싱하는 인프라 서비스입니다.

Gemini가 설명한 SDX → Unity Catalog 전환에서:
- Ranger 감사 로그 인덱싱(CDP-INFRA-SOLR) → **Unity Catalog 내장 감사 기능 + System Tables**
- 별도 Solr 인프라를 운영할 필요 없이 플랫폼에 내장됨

### Databricks 관점
Unity Catalog는 모든 자산에 대한 접근 이력을 자동으로 추적합니다.
외부 로그 분석이 필요한 경우 Splunk, Elastic, Azure Monitor 같은 도구와 연동합니다.

## Gemini 관점 요약

CDP-INFRA-SOLR은 Gemini 답변에서 독립 서비스로 비교되지 않았습니다.
상세 비교는 GPT 답변(`gpt.md`) 또는 Claude 정리(`claude.md`)를 참고하세요.
