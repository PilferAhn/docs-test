# SDX - Shared Data Experience (GPT 답변)

> 출처: ChatGPT 답변 원문
> GPT는 SDX를 직접 비교하지 않고, SDX를 구성하는 핵심 컴포넌트(Ranger)를 중심으로 설명했습니다.

## GPT가 다룬 관련 컴포넌트

SDX는 다음 컴포넌트들을 CDP 상위 서비스로 묶은 것입니다.

### Ranger → Unity Catalog
- Ranger: 플랫폼 전반의 데이터 보안 관리 프레임워크
- 대응: **Unity Catalog** (비교적 직접적인 대응)
- 상세 내용: `07_Ranger/gpt.md` 참고

### CDP-INFRA-SOLR → Unity Catalog 감사 기능
- CDP-INFRA-SOLR: Ranger 감사 로그 인덱싱 서비스
- 대응: **Unity Catalog 내장 감사 기능 + System Tables**
- 상세 내용: `14_CDP-INFRA-SOLR/gpt.md` 참고

## GPT 관점 요약

SDX를 구성하는 핵심 컴포넌트들의 대응 관계:
- **Ranger(접근 권한)** → **Unity Catalog** (권한 관리 내장)
- **Audit 로그(SOLR)** → **Unity Catalog System Tables**
- (Atlas는 GPT 답변에서 별도로 다루지 않았으나, Unity Catalog의 lineage 기능이 대응)
