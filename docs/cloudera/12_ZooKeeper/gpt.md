# ZooKeeper (GPT 답변)

> 출처: ChatGPT 답변 원문

## Cloudera에서의 역할

ZooKeeper는 Hadoop 생태계의 고전적인 **분산 코디네이션 서비스**입니다.
여러 분산 컴포넌트가 서로를 찾고 상태를 맞추고 리더 선출을 할 때 쓰는 기반 인프라입니다.
YARN 관련 ZooKeeper ACL이 자동 구성될 정도로, 여러 서비스의 뒤에서 동작합니다.

### 실제 역할 상세
- 리더 선출
- 서비스 디스커버리
- 설정/상태 동기화
- 분산 락/coordination
- HBase, Kafka, 일부 YARN/Hadoop 구성요소의 보조 인프라

## Databricks 대응

대부분 **Databricks가 숨기는 내부 플랫폼 기능**입니다.

사용자는 Databricks에서 ZooKeeper를 직접 운영하지 않습니다.
이 종류의 분산 코디네이션은 Databricks 관리 서비스와 클라우드 네이티브 제어 계층 내부로 흡수되어 있습니다.

- **직접 대응 없음**
- **Databricks control plane / managed platform internals에 해당**

## 한 줄 매핑

**ZooKeeper ≈ Databricks 내부 관리형 coordination layer**
사용자가 직접 보는 대응 서비스는 없음
