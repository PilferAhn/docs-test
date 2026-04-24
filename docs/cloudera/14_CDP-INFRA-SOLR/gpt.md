# CDP-INFRA-SOLR (GPT 답변)

> 출처: ChatGPT 답변 원문

## Cloudera에서의 역할

이건 일반적인 "사용자 검색 서비스"라기보다, Cloudera 운영 관점에서 자주 보이는 **인프라용 Solr 서비스**입니다.
**Infra Solr가 Ranger audit 로그를 인덱싱하고 저장하는 데 쓰이는 Solr 서비스**입니다.
Infra-Solr는 `ranger_audits` 같은 민감하고 트래픽 많은 컬렉션을 올려두는 용도이므로, **커스텀 워크로드용으로 쓰는 것을 권장하지 않는다**고 명시합니다.

즉, "비즈니스 검색 엔진"보다는 **감사 로그 검색/보관용 인덱스 백엔드**에 가깝습니다.

### 실제 역할 상세
- Ranger가 남기는 감사 이벤트를 빠르게 검색 가능하게 만듦
- "누가 어떤 Hive 테이블을 읽었는지", "누가 HDFS 경로 접근을 시도했는지" 등 보안/감사 추적
- 운영자가 장애 분석이나 보안 포렌식할 때 활용

## Databricks 대응

**가장 가까운 대응은 Databricks의 감사/거버넌스/모니터링 계층**이지, 특정 "Solr 서비스"가 아닙니다.

1. **Ranger audit 검색 역할** → Databricks에서는 **audit logs + Unity Catalog 거버넌스 이벤트 + system tables/모니터링 체계**
2. **인덱싱 엔진 자체** → Databricks는 사용자가 별도 Solr를 직접 운영하는 방식이 기본 구조가 아님. 필요하면 외부 검색/로그 분석 플랫폼을 붙임
3. **보안 이벤트 추적** → Unity Catalog 중심의 권한/계보/접근 가시성이 핵심

## 한 줄 매핑

**CDP-INFRA-SOLR ≈ Databricks의 내장 거버넌스·감사 관측 영역 + 필요시 외부 로그 분석 시스템**
정확한 1:1 서비스는 없음
