# Ranger (GPT 답변)

> 출처: ChatGPT 답변 원문

## Cloudera에서의 역할

Ranger는 **플랫폼 전반의 데이터 보안을 enable/monitor/manage 하는 프레임워크**입니다.
정책 기반 접근 제어를 여러 서비스(HDFS, Hive 등)에 걸쳐 관리합니다.
정책은 resource-based와 tag-based가 있으며, Ranger RMS를 통해 Hive 정책과 HDFS ACL 동기화도 지원합니다.

### 실제 역할 상세
- 사용자/그룹별 권한 정책 정의
- HDFS, Hive, HBase 등 서비스별 접근 제어
- 감사(audit) 로그 생성
- 보안 관리자 중심의 중앙 정책 관리

## Databricks 대응

가장 직접적인 대응은 **Unity Catalog**입니다.

Unity Catalog는 Databricks에 내장된 통합 데이터/AI 거버넌스 솔루션입니다.
catalog, schema, table, volume, model, function 등 다양한 객체에 대해 중앙 권한 관리가 가능하고, lineage도 제공합니다.

### 차이점
- Ranger: Hadoop 생태계 여러 독립 서비스를 가로질러 붙는 보안 프레임워크
- Unity Catalog: Databricks 플랫폼 내부의 기본 거버넌스 계층
- Ranger보다 객체 모델이 더 Databricks-native하고, 데이터/AI 자산 전반을 한 번에 묶음

## 한 줄 매핑

**Ranger ≈ Unity Catalog**
이 또한 꽤 직접적인 대응입니다.
