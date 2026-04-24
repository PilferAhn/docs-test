# Cloudera vs Databricks 전체 매핑 (GPT 답변)

> 출처: ChatGPT 답변 원문 정리

## 큰 전제

Cloudera의 각 서비스와 Databricks는 1:1로 정확히 대응되지 않습니다.
Cloudera는 전통적인 Hadoop 생태계의 **개별 인프라 컴포넌트들을 직접 운영**하는 구조에 가깝고,
Databricks는 그 위 기능 상당수를 **통합 플랫폼 형태로 추상화**해 제공합니다.

## 전체 매핑 요약

| Cloudera 서비스 | Databricks 대응 |
|:---|:---|
| HDFS | S3/ADLS/GCS + Delta Lake + Unity Catalog external locations |
| Hive Metastore | Unity Catalog metastore |
| Hive on Tez | Databricks compute(Spark) + SQL warehouse |
| Impala | Databricks SQL warehouse |
| Kudu | Delta Lake |
| Oozie | Lakeflow Jobs |
| Ranger | Unity Catalog |
| Hue | Notebook + SQL Editor + Catalog Explorer |
| Tez | Spark execution layer (내부 실행 엔진) |
| YARN | Databricks compute/resource management plane |
| YARN Queue Manager | compute policies + warehouse scaling/queuing governance |
| ZooKeeper | Databricks 내부 관리형 coordination |
| Core Configuration | Databricks control plane/workspace-wide config |
| CDP-INFRA-SOLR | Databricks 감사/거버넌스 관측 계층 + 필요시 외부 로그 분석 시스템 |

## 전환 관점에서 가장 중요한 해석

Cloudera에서 Databricks로 넘어갈 때 핵심은 "서비스 이름 치환"이 아니라 **아키텍처 사고방식의 전환**입니다.

### Cloudera의 사고방식
- 저장소는 HDFS
- 메타는 HMS
- 보안은 Ranger
- SQL은 Hive/Impala
- 실행엔진은 Tez/Spark
- 스케줄링은 Oozie
- 리소스 관리는 YARN
- 운영 보조는 ZooKeeper/Solr

### Databricks의 사고방식
- 저장소는 클라우드 오브젝트 스토리지
- 테이블 계층은 Delta Lake
- 메타/권한/계보는 Unity Catalog
- SQL은 SQL warehouse
- 엔지니어링 실행은 compute
- 스케줄링은 Lakeflow Jobs
- 내부 코디네이션/자원 관리는 플랫폼이 숨김
