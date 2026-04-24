# Core Configuration (GPT 답변)

> 출처: ChatGPT 답변 원문

## Cloudera에서의 역할

현재 문서에서는 이 서비스가 **Core Settings service로 이름이 바뀌었다**고 설명합니다.
역할은 **클러스터 전역 설정 저장소**입니다.

예전에는 일부 서비스가 HDFS를 반드시 필요로 했던 이유가 "공통 설정 파일을 배포해야 해서"였는데,
Core Settings/Core Configuration이 그 역할을 대신하면서 **HDFS 없이도 클러스터를 만들 수 있게 해주는 기반 서비스**입니다.

### 실제 역할 상세
- 클러스터 전체가 공유해야 하는 설정을 저장
- 어떤 서비스가 시작될 때 참조하는 공통 설정/구성 파일 배포의 중심 역할
- 과거 Hadoop에서 HDFS가 "공통 설정 배포 저장소" 역할 일부를 하던 것을 분리해낸 개념

## Databricks 대응

Databricks에는 이것과 정확히 똑같은 독립 서비스가 거의 없습니다.
이런 역할이 **플랫폼 컨트롤 플레인과 워크스페이스/컴퓨트 설정 시스템 안으로 흡수**되어 있기 때문입니다.

가장 가까운 개념들:
- **Workspace-level 설정**
- **Compute 정책 / cluster configuration**
- **SQL warehouse 설정**
- **Unity Catalog 메타스토어/거버넌스 설정**

### 핵심 차이
- Cloudera: "설정 저장 서비스"가 눈에 보이는 별도 서비스
- Databricks: 플랫폼이 그걸 숨기고 자동으로 제공

## 한 줄 매핑

**Core Configuration ≈ Databricks control plane의 workspace/compute/global configuration**
독립 서비스로 대응되지는 않음
