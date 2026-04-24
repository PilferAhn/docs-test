# ZooKeeper (Claude 정리)

> GPT 답변 + Gemini 답변을 종합 정리한 버전

## ZooKeeper란?

**분산 서비스들이 서로 상태를 맞추고 조율하는 "보조 인프라"** 입니다.

사용자가 직접 "ZooKeeper 써!"라고 하지 않지만,
Hadoop 생태계의 많은 서비스들이 **뒤에서 자동으로** ZooKeeper를 활용합니다.

## ZooKeeper가 하는 일 (쉬운 비유)

| ZooKeeper 기능 | 실생활 비유 |
|:---|:---|
| 리더 선출 | 여러 후보 중 "대표" 한 명 자동 선출 |
| 서비스 디스커버리 | "저 서비스는 어느 서버에 있나?" 전화번호부 |
| 상태 동기화 | 여러 서버가 같은 시계를 보도록 맞추기 |
| 분산 락 | 동시에 같은 자원에 접근 못하게 잠금 |

## Cloudera에서의 역할

GPT 관점:
- 사용자에게는 별도 서비스로 표시됨
- HBase, Kafka, YARN 등의 보조 인프라로 동작
- 운영자가 ZooKeeper 상태를 모니터링해야 함

Gemini 추가 관점:
- Cloudera는 도구의 다양성 — ZooKeeper도 별도 관리 서비스
- Databricks는 엔진의 통일성 — 이런 인프라가 모두 숨겨짐

## Databricks 대응

GPT와 Gemini 모두 동일한 결론:
**ZooKeeper에 대응하는 사용자 노출 서비스가 없으며, 플랫폼 내부로 완전히 흡수됩니다.**

Databricks에서는 다음이 ZooKeeper의 역할을 대신합니다.
- 클라우드 관리형 서비스 (AWS/Azure/GCP의 분산 코디네이션 레이어)
- Databricks 컨트롤 플레인의 내부 관리 기능

사용자는 이것을 전혀 의식하지 않습니다.

## 한 줄 요약

**ZooKeeper ≈ Databricks 내부 coordination 레이어**
(사용자에게 보이는 대응 서비스 없음, 완전히 추상화됨)
