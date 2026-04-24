# Ranger (Gemini 답변)

> 출처: Gemini 답변 원문
> Gemini는 Ranger를 SDX(Shared Data Experience) 카테고리 안에서 Apache Atlas와 함께 다뤘습니다.

## SDX (Shared Data Experience) — Ranger 포함

### Cloudera SDX 설명
Apache **Ranger**와 **Atlas**를 기반으로 합니다.
"한 번 설정하면 어디서든 적용된다"는 원칙 하에 하이브리드 클라우드 전체의 보안 정책과 데이터 카탈로그를 통합 관리합니다.

- **Apache Ranger**: 접근 권한 정책 관리 (누가 어떤 데이터에 접근할 수 있는지)
- **Apache Atlas**: 데이터 카탈로그 및 계보(Lineage) 관리 (데이터가 어디서 와서 어디로 갔는지)

### Databricks 대응: Unity Catalog
- Databricks의 모든 자산(파일, 테이블, 모델, 대시보드)에 대한 통합 거버넌스 레이어
- **Delta Sharing** 기능으로 클라우드 간 데이터 공유가 매우 강력
- 최근에는 AI 모델 거버넌스까지 확장

### 주요 차이점
| 항목 | SDX (Ranger + Atlas) | Unity Catalog |
|:---|:---|:---|
| 권한 관리 | Apache Ranger | 내장 |
| 데이터 계보 | Apache Atlas | 내장 (자동 추적) |
| 적용 환경 | 하이브리드 (온프레미스+클라우드) | 클라우드 네이티브 최적화 |
| AI 자산 거버넌스 | 제한적 | 강력 (모델, 함수 포함) |
