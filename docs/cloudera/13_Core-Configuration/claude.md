# Core Configuration (Claude 정리)

> GPT 답변 + Gemini 답변을 종합 정리한 버전

## Core Configuration이란?

클러스터 안의 모든 서비스가 공통으로 참조해야 하는 **설정값들을 저장하고 배포하는 서비스**입니다.

회사 전체 직원이 공유하는 **사내 규정집**에 비유할 수 있습니다.
어떤 서비스가 새로 시작될 때 "공통 설정이 뭐더라?"를 여기서 읽어갑니다.

## Cloudera에서의 역할

GPT 관점:
- 클러스터 전체 공유 설정 저장 및 배포
- 이전에는 HDFS가 이 역할 일부를 담당했으나, Core Configuration이 독립 서비스로 분리됨
- 현재 이름은 **Core Settings**로 변경됨
- HDFS 없이도 클러스터 구성을 가능하게 하는 기반 역할

## Databricks 대응

GPT 관점: 플랫폼 컨트롤 플레인 안으로 흡수
Gemini 관점: "도구의 다양성 → 엔진의 통일성" 전환 — 설정 서비스가 별도로 보이지 않음

| Core Configuration 역할 | Databricks 대응 |
|:---|:---|
| 클러스터 전역 설정 저장 | Workspace-level 설정 (컨트롤 플레인) |
| 공통 설정 배포 | 플랫폼이 자동 처리 |
| Compute 구성 설정 | Compute 정책 / Cluster configuration |
| SQL 실행 환경 설정 | SQL Warehouse 설정 |
| 거버넌스 설정 | Unity Catalog 메타스토어 설정 |

### 핵심 차이
Cloudera에서는 이 서비스가 별도로 눈에 보이지만,
Databricks에서는 사용자가 이런 개념 자체를 의식할 필요가 없습니다.

## 한 줄 요약

**Core Configuration ≈ Databricks 컨트롤 플레인의 Workspace/Compute 설정**
(독립 서비스 대응 없음, 플랫폼이 자동 흡수)
