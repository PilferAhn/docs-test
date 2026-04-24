# SDX - Shared Data Experience (Gemini 답변)

> 출처: Gemini 답변 원문

## 5. 거버넌스 & 보안 (Security & Governance)

전사 데이터의 권한 관리와 계보(Lineage)를 관리합니다.

### Cloudera SDX (Shared Data Experience)
Apache Ranger와 Atlas를 기반으로 합니다.

**핵심 원칙**: "한 번 설정하면 어디서든 적용된다"
하이브리드 클라우드 전체의 보안 정책과 데이터 카탈로그를 통합 관리합니다.

| SDX 구성 요소 | 역할 |
|:---|:---|
| **Apache Ranger** | 접근 권한 정책 관리 |
| **Apache Atlas** | 데이터 카탈로그 및 계보(Lineage) 관리 |

### Databricks 대응: Unity Catalog
Databricks의 모든 자산(파일, 테이블, 모델, 대시보드)에 대한 **통합 거버넌스 레이어**입니다.

- **Delta Sharing**: 클라우드 간 데이터 공유 기능이 매우 강력
- 최근 AI 모델 거버넌스까지 확장됨

### 주요 차이점
| 항목 | SDX (Ranger + Atlas) | Unity Catalog |
|:---|:---|:---|
| 권한 관리 | Apache Ranger | 내장 |
| 데이터 카탈로그 | Apache Atlas | 내장 (자동 추적) |
| 적용 환경 | 하이브리드 클라우드 최적화 | 클라우드 네이티브 최적화 |
| AI 자산 관리 | 제한적 | 강력 (모델, 함수 포함) |
| 클라우드 간 공유 | 제한적 | Delta Sharing으로 강력 지원 |
