# Ranger (Claude 정리)

> GPT 답변 + Gemini 답변을 종합 정리한 버전

## Ranger란?

**플랫폼 전반의 데이터 보안을 관리하는 프레임워크**입니다.

회사 건물의 **출입 통제 시스템**에 비유할 수 있습니다.
어떤 직원(사용자)이 어떤 방(데이터)에 들어갈 수 있는지 정책을 정의하고, 모든 출입 기록을 남깁니다.

## Cloudera에서의 역할

GPT 관점 (컴포넌트 수준):
- 사용자/그룹별 접근 권한 정책 정의
- HDFS, Hive, HBase 등 여러 서비스에 걸친 접근 제어
- 감사(Audit) 로그 생성
- Resource-based 정책 + Tag-based 정책 지원
- Ranger RMS: Hive 정책과 HDFS ACL 동기화

Gemini 관점 (SDX 카테고리):
- SDX = Ranger(권한) + Atlas(계보) 조합
- "한 번 설정하면 어디서든 적용" — 하이브리드 클라우드 전체 통합 관리

## Databricks 대응

GPT와 Gemini 모두 **Unity Catalog**를 직접 대응으로 지목합니다.

| 항목 | Ranger (+ Atlas) | Unity Catalog |
|:---|:---|:---|
| 권한 관리 | ✅ Ranger가 담당 | ✅ 내장 |
| 감사 로그 | ✅ Infra-Solr에 인덱싱 | ✅ System Tables |
| 데이터 계보 | ✅ Atlas가 담당 | ✅ 자동 추적 내장 |
| AI 자산 관리 | ❌ | ✅ (모델, 함수 포함) |
| 적용 환경 | 하이브리드 (온프레미스+클라우드) | 클라우드 네이티브 |
| 클라우드 간 공유 | 제한적 | ✅ Delta Sharing |

### 핵심 차이
- **Ranger**: 여러 독립 서비스를 가로질러 붙는 외부 보안 프레임워크
- **Unity Catalog**: Databricks 내부에 기본으로 내장된 거버넌스 계층

## 한 줄 요약

**Ranger ≈ Unity Catalog** (비교적 직접적인 대응, 그러나 Unity Catalog가 더 넓은 범위)
