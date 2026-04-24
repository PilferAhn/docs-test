# CDP-INFRA-SOLR (Claude 정리)

> GPT 답변 + Gemini 답변을 종합 정리한 버전

## CDP-INFRA-SOLR이란?

**보안 감사(Audit) 로그를 빠르게 검색할 수 있도록 인덱싱하는 전용 Solr 서비스**입니다.

이름에 "SOLR"이 들어가서 일반 검색 엔진처럼 보이지만, 실제로는 **Ranger가 기록한 보안 이벤트 로그를 전문적으로 처리하는 인프라 서비스**입니다.

> 중요: Cloudera가 공식 문서에서 "커스텀 워크로드에 사용하지 말라"고 명시하는 운영자 전용 인프라입니다.

## Cloudera에서의 역할

GPT 관점:
- Ranger 감사 이벤트를 인덱싱하여 빠른 검색 지원
- "누가 어떤 테이블을 읽었나?", "보안 정책 위반이 있었나?" 추적
- 운영자·보안팀의 포렌식 도구
- `ranger_audits` 컬렉션이 핵심 데이터

Gemini 추가 관점 (SDX 맥락):
- SDX(Ranger+Atlas)의 감사 기능 중 일부를 담당
- Databricks 전환 시 Unity Catalog의 내장 감사 기능으로 대체 가능

## Databricks 대응

GPT와 Gemini 모두 동일하게, **직접 대응하는 단일 서비스가 없습니다.**

| CDP-INFRA-SOLR 역할 | Databricks 대응 |
|:---|:---|
| Ranger 감사 로그 인덱싱 | **Unity Catalog 내장 감사 기능** |
| 접근 이력 검색 | **Databricks System Tables** (SQL로 조회 가능) |
| 보안 이벤트 추적 | **Audit Log Delivery** (클라우드 스토리지 연동) |
| 외부 SIEM 연동 | Splunk, Elastic, Azure Monitor 등 외부 도구 |

### 핵심 차이
- Cloudera: 별도 Solr 인프라를 직접 운영해야 함
- Databricks: 감사 기능이 플랫폼에 내장, System Tables로 SQL 조회 가능

## 한 줄 요약

**CDP-INFRA-SOLR ≈ Unity Catalog 내장 감사 기능 + System Tables**
(직접 대응 서비스 없음, 별도 Solr 운영 불필요)
