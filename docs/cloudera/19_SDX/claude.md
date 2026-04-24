# SDX - Shared Data Experience (Claude 정리)

> GPT 답변 + Gemini 답변을 종합 정리한 버전

## SDX란?

**전사 데이터의 보안 정책과 거버넌스를 통합 관리하는 Cloudera의 핵심 서비스**입니다.

"한 번 설정하면 어디서든 적용된다"는 원칙으로, 하이브리드 클라우드 전체에 걸쳐 보안과 데이터 카탈로그를 일관되게 제공합니다.

## Cloudera에서의 역할

SDX = Apache Ranger + Apache Atlas

| 구성 요소 | 역할 | 설명 |
|:---|:---|:---|
| **Apache Ranger** | 접근 권한 관리 | 누가 어떤 데이터에 접근할 수 있는지 정책 정의 |
| **Apache Atlas** | 데이터 계보(Lineage) | 데이터가 어디서 왔고 어디로 갔는지 추적 |

GPT의 컴포넌트 수준 설명:
- Ranger: resource-based + tag-based 정책, Ranger RMS로 Hive/HDFS ACL 동기화
- CDP-INFRA-SOLR: Ranger 감사 로그의 인덱싱 (SDX의 감사 기반 인프라)

## Databricks 대응

GPT와 Gemini 모두 **Unity Catalog**를 명확한 대응으로 지목합니다.

| SDX 기능 | Databricks Unity Catalog |
|:---|:---|
| Ranger: 접근 권한 정책 | **내장 GRANT/REVOKE 권한 관리** |
| Atlas: 데이터 계보 | **자동 Lineage 추적 내장** |
| 데이터 카탈로그 | **Catalog Explorer** |
| 감사 로그(Solr) | **System Tables (SQL로 조회)** |
| AI 자산 거버넌스 | **모델, 함수, 볼륨까지 포함** |
| 클라우드 간 공유 | **Delta Sharing** |

### 두 관점의 핵심 차이 정리

**GPT 관점** (컴포넌트 수준):
- Ranger → Unity Catalog (직접 대응)
- 각 기능이 독립 컴포넌트 → Unity Catalog에 통합됨

**Gemini 관점** (서비스 수준):
- SDX의 "하이브리드 클라우드 통합 거버넌스" 강점 강조
- Unity Catalog는 클라우드 네이티브에 최적화

### 선택 시 고려사항
- **온프레미스 + 클라우드 병행 필요** → SDX가 더 유리
- **퍼블릭 클라우드 중심** → Unity Catalog가 더 고도화

## 한 줄 요약

**SDX ≈ Unity Catalog**
(Ranger+Atlas의 개별 서비스 → Unity Catalog의 통합 거버넌스 레이어)
