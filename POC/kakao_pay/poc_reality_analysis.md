# 카카오페이 PoC — 시나리오별 현실 분석

> **작성 목적:** poc_overview.md에 기술된 시나리오들을 객관적으로 재검토하여,
> 실제 PoC 환경에서 각 항목이 어디까지 구현 가능한지 정의한다.

---

## 전제 조건

| 항목 | 내용 |
|:---|:---|
| PoC 기간 | 9일 |
| 투입 인력 | Databricks SE 팀 단독 |
| 카카오페이 엔지니어 참여 | 없음 (데이터 제공 역할만) |
| 데이터 접근 방식 | 카카오페이가 사전 추출·마스킹하여 S3에 업로드 |
| 온프렘 직접 접근 | 불가 (VPN 미확정, 금융사 보안 정책) |
| 카카오페이 내부 시스템 수정 | 불가 (Tiara, Kafka, Debezium, Minecraft 등) |

---

## 전체 시나리오 현실 분석 테이블

| 시나리오 | 목적 요약 | 한계 정의 | 실제 구현 방법 |
|:---|:---|:---|:---|
| **A-1** Kafka → Delta 실시간 적재 | 티아라 행동로그를 Kafka에서 실시간으로 Delta에 적재 | Kafka가 카카오페이 온프렘에 있어 직접 연결 불가. Tiara 시스템을 Databricks로 이중 전송하도록 수정 불가 | 카카오페이가 S3에 올려준 Kafka 토픽 캡처 파일을 Auto Loader로 읽는 방식으로 스트리밍 시뮬레이션 |
| **A-2** Iceberg → Delta 전환 | 기존 Iceberg 포맷 데이터를 Delta Lake로 변환 | CEPH의 실제 Iceberg 파일에 직접 접근 불가 | 카카오페이가 S3에 올려준 특정 기간(10/20~10/26) Iceberg 파일을 Spark으로 읽어 Delta 변환. 가장 현실적으로 구현 가능한 시나리오 |
| **A-3** Kudu → Delta 전환 | Kudu 테이블을 Spark Connector로 읽어 Delta 변환 | Kudu는 온프렘 전용 스토리지. Spark Kudu Connector로 온프렘 직접 연결 불가 | 카카오페이가 Kudu 데이터를 Parquet/CSV로 추출하여 S3에 올려주면 Delta로 변환하는 방식. Kudu 실시간 연결 없음 |
| **B** ETL / 배치 파이프라인 전환 | 기존 Hive/Kudu 기반 ETL 45개 테이블(36TB)을 Databricks로 재현 | 실제 ETL 로직(SQL)은 카카오페이 내부 코드. 36TB 전체를 9일 내 처리 불가 | 카카오페이가 제공한 대표 SQL 일부를 Databricks Notebook으로 재작성하는 데모 수준. 실제 36TB 대신 샘플 데이터 사용 |
| **C** 성능 비교 | Impala/Trino/StarRocks vs Databricks SQL/Photon 수치 비교 | 기존 시스템(Impala, Trino, StarRocks) 성능 수치는 카카오페이가 직접 제공해야 함. 동일 조건 벤치마크 구성 불가 | Databricks 측 성능만 측정. 카카오페이가 제공한 기존 수치와 단순 비교. TPC-H 1TB는 공개 데이터셋으로 별도 측정 가능 |
| **D** SQL Warehouse / BI 연동 | MSTR이 Databricks SQL Warehouse에 JDBC로 연결하여 기존처럼 조회 | MSTR은 카카오페이 내부 라이선스/환경. MSTR 클라이언트 없이 큐브 테스트 불가 | JDBC 연결 설정 및 토큰 발급 절차 데모. 실제 MSTR 큐브 쿼리 테스트는 카카오페이 측에서 수행해야 함 |
| **E** 실시간 조회 / 서빙 (100ms) | StarRocks 기준 100ms 미만 응답 시간을 Databricks SQL Warehouse로 달성 | Databricks SQL Warehouse는 분석/BI 워크로드에 최적화. 초저지연 OLAP 서빙 영역이 아님. 달성 가능성 낮음 | 워밍업된 SQL Warehouse에서 단순 집계 쿼리 응답 시간 측정 후 수치 제시. 100ms 달성 불가 시 목표 완화 협의가 병행되어야 함 |
| **F** DLT / Streaming Table | DLT로 스트리밍 적재 파이프라인 구성 및 Materialized View 동기화 검증 | 실제 Kafka 스트림 연결 불가 | S3 파일 기반 Auto Loader → DLT → Delta 파이프라인 구성 데모. Materialized View 동기화 기능은 정적 데이터로도 시연 가능 |
| **G** 스키마 변경 | 7TB 테이블 무중단 컬럼 추가/삭제/타입 변경 1시간 이내 | 7TB 실제 데이터 없으면 의미 있는 소요시간 측정 불가 | 소규모 데이터(수십 GB)로 DDL 기능 시연 후 성능 외삽으로 추정치 제시. 기능 자체는 구현 가능하나 수치의 신뢰도 낮음 |
| **H** CDC 처리 | MySQL binlog → Debezium → Kafka → DLT 실시간 CDC 파이프라인 구성 | MySQL/Debezium/Kafka 전부 카카오페이 온프렘. 파이프라인 수정 불가. 직접 연결 불가 | 카카오페이가 S3에 올려준 CDC 이벤트 파일(JSON/Avro)을 DLT로 읽어 Merge 처리하는 데모. 실시간 CDC가 아닌 배치 replay |
| **I** 탈퇴자 삭제 / 컴플라이언스 | 84TB에서 12만 건을 48시간 이내 삭제하면서 동시 스트리밍 유지 | 84TB 실제 데이터 없음. 동시 스트리밍 없으면 충돌 검증 불가. PoC에서 가장 중요한 시나리오이나 조건 재현 불가 | 소규모 데이터(수십 GB)로 Deletion Vectors + Liquid Clustering 기반 삭제 기능 시연. 동시성 시뮬레이션은 Notebook 내 병렬 실행으로 제한적 재현 |
| **J** 보안 / 권한 / 컴플라이언스 | Unity Catalog 권한·마스킹, QueryPie 연동, 샤카 API 연동 | QueryPie/샤카는 카카오페이 내부 시스템. 실제 연동 테스트 불가 | Unity Catalog Row Filtering, Column Masking, Audit Log 기능 데모. QueryPie/샤카 연동은 아키텍처 설계 문서로 대체 |
| **K** 인프라 / 클라우드 구성 | AWS 클라우드 구성, Keycloak → AWS SSO → Databricks SSO 체인, Kerberos 연동 | Keycloak은 카카오페이 내부. Kerberos 인증은 온프렘 KDC에 접근해야 가능. 두 항목 모두 카카오페이 협조 없이 불가 | Databricks Workspace + Unity Catalog + S3 버킷 구성은 가능. SSO 체인은 설정 가이드 문서 제공으로 대체. Kerberos 연동은 데모 불가 |
| **L** 데이터 이관 | DistCp로 HDFS → S3 직접 복제, 이관 속도 및 병목 검증 | HDFS에 직접 접근 불가. DistCp는 카카오페이 온프렘에서 실행해야 함 | 카카오페이가 S3에 올려준 데이터 기준으로 Delta 변환 작업만 수행. DistCp 자체는 카카오페이 내부 실행. 이관 속도 측정 불가 |
| **M** 데이터 아키텍처 / 저장 포맷 | Delta Lake vs Iceberg 성능 비교, Liquid Clustering, Deletion Vectors, 행 수준 동시성 | 없음. Databricks 환경 내에서 자체 검증 가능 | 제공된 데이터로 포맷 비교, Liquid Clustering, Deletion Vectors 실제 성능 측정. 9일 내 가장 완성도 높게 구현 가능한 시나리오 |
| **N** 비용 / TCO 최적화 | Spot Instance, Serverless vs Classic SQL Warehouse 비용 비교 | Serverless는 CSP 평가 미완료로 금융사 사용 불가. 실제 운영 워크로드 없이 정확한 비용 산정 어려움 | Classic SQL Warehouse 기준 비용 측정만 가능. Serverless 수치는 Databricks 공식 자료로 대체. Spot Instance 설정 데모 |
| **O** 모니터링 / 관제 | Grafana/CloudWatch 연동, Slack 알람, QueryPie Audit Log 연동 | 카카오페이 내부 Grafana/Slack 워크스페이스 접근 불가 | UC System Tables 기반 쿼리 이력/비용 조회, Workflow 실패 알람 기능 데모. 외부 시스템 연동은 아키텍처 문서로 대체 |
| **P-1** ML 파이프라인 이관 (BM Index) | 기존 BM Index 모델 2개를 MLflow에 등록하고 2,000만 유저 배치 추론 | 실제 모델 파일(Pickle/H5)과 학습 데이터가 있어야 함. 카카오페이가 S3에 올려줘야 진행 가능 | 카카오페이가 S3에 올려준 모델 파일을 MLflow에 등록하고 소규모 샘플로 추론 실행 데모. 2,000만 유저 전체 배치는 시간상 불가 |
| **P-2** 신규 LAL PoC | LAL 모델 구성, Feature Store, Vector Search, CTR Prediction 실시간 서빙 (100ms) | 실제 유저 데이터 없음. Feature Store 구성 자체가 별도 프로젝트급 공수. 100ms 실시간 서빙은 E 시나리오와 동일한 이유로 달성 어려움 | Feature Store 아키텍처 설계 문서 제공. Vector Search 기능 데모 수준. 실제 LAL 모델 학습/서빙은 PoC 범위 초과 |

---

## 시나리오별 상세 분석

---

### A-1. Kafka → Delta Lake 실시간 적재

**목적**
티아라(Tiara) 행동로그 시스템이 Kafka로 흘려보내는 데이터를 Databricks Structured Streaming으로 수신하여 Delta Lake에 실시간 적재하는 파이프라인을 검증한다. 초당 4.5만 건, 230GB/day 규모의 처리 성능과 Exactly-Once 보장을 확인하는 것이 핵심이다.

**왜 그대로 구현이 안 되는가**
- Tiara는 카카오페이 내부 행동로그 수집 시스템이며, 현재 카카오페이 온프렘 Kafka 클러스터로 데이터를 전송하도록 구성되어 있다.
- 이 시스템이 Databricks로도 동시에 전송하려면 Tiara 내부 설정 또는 Kafka 파이프라인을 수정해야 하는데, 이는 카카오페이 내부 엔지니어링 작업이다.
- VPN을 통해 온프렘 Kafka에 Databricks Consumer를 붙이는 방법도 있으나, 금융사 보안 정책상 외부 서비스가 내부 Kafka에 Consumer로 등록되는 것을 허용하기 어렵다.
- Action Item #2(VPN 연결 및 대역폭 확보)가 TBD 상태인 것이 이를 반증한다.

**실제 구현**
카카오페이가 사전에 Kafka 토픽에서 캡처한 데이터를 JSON/Avro 파일로 S3에 업로드하면, Databricks Auto Loader로 S3 파일을 읽어 Structured Streaming처럼 동작하도록 시뮬레이션한다. 실제 실시간 스트리밍이 아닌 파일 기반 replay이므로, 초당 4.5만 건 처리 성능이나 Exactly-Once 보장은 실제 환경과 동일하게 검증되지 않는다.

---

### A-2. Iceberg → Parquet → Delta 전환

**목적**
카카오페이가 CEPH에 Iceberg 포맷으로 저장 중인 티아라 로그 테이블(`tiara_complete_log_raw`, `tiara_ns`)을 Spark으로 읽어 Delta Lake 포맷으로 변환하는 이관 작업을 검증한다.

**왜 그대로 구현이 안 되는가**
- CEPH는 카카오페이 온프렘 오브젝트 스토리지이므로 직접 접근 불가.
- CEPH가 S3 호환이므로 카카오페이 측이 API를 열어주거나 직접 S3로 복사해줘야 Databricks에서 읽을 수 있다.

**실제 구현**
전체 시나리오 중 현실적으로 가장 완성도 있게 구현 가능하다. 카카오페이가 지정 기간(10/20~10/26)의 Iceberg 파일을 PoC용 S3 버킷에 올려주면, Databricks Spark으로 Iceberg 파일을 읽어 Delta로 변환하는 전체 흐름을 실제로 실행할 수 있다. 이관 성능, 포맷 변환 시간, 메타데이터 처리 방식도 실측 가능하다.

---

### A-3. Kudu → Delta 전환

**목적**
Cloudera 전용 스토리지인 Kudu 테이블을 Spark Kudu Connector로 읽어 Delta Lake로 변환한다. Kudu는 실시간 CRUD를 지원하는 컬럼형 스토리지로, 파일 직접 복사가 불가능하여 Connector 경유가 필수다.

**왜 그대로 구현이 안 되는가**
- Spark Kudu Connector는 온프렘 Kudu Master 서버 주소로 직접 TCP 연결을 맺는 구조다.
- Kudu가 온프렘에 있고 VPN 없이 Databricks(AWS)에서 연결하는 것이 불가능하다.
- 설령 VPN이 허용되더라도 금융사 내부 DB 서버에 외부 Compute가 직접 붙는 것은 보안 심의 통과가 매우 어렵다.

**실제 구현**
카카오페이가 Kudu 데이터를 Parquet 또는 CSV로 추출하여 S3에 올려주면, 그 파일을 Databricks에서 읽어 Delta로 변환하는 작업만 수행한다. Kudu Connector를 통한 실시간 연결은 이루어지지 않으며, Kudu 고유의 실시간 CRUD 특성(순서 보장, 동시 업데이트)은 검증 대상에서 제외된다.

---

### B. ETL / 배치 파이프라인 전환

**목적**
카카오페이가 현재 Hive, Kudu, Tiara 기반으로 운영 중인 45개 테이블, 36TB 규모의 ETL 파이프라인(티아라, 마이데이터, 결제, 머니 도메인)을 Databricks로 재현하고, Airflow Databricks Operator 호환성을 확인한다.

**왜 그대로 구현이 안 되는가**
- 45개 ETL SQL 로직은 카카오페이 내부 코드다. SE 팀이 보유하고 있지 않으며, 카카오페이가 제공하지 않으면 재현 불가.
- 36TB 전체 데이터를 9일 내에 적재하고 ETL을 실행하는 것 자체가 시간적으로 불가능하다.
- 기존 병목(Impala row_number, Heavy UDF, JSON Parsing) 재현에는 실제 운영 규모와 동일한 데이터가 필요하다.

**실제 구현**
카카오페이가 제공하는 대표 SQL 몇 개를 Databricks Notebook으로 재작성하여 실행하는 데모 수준으로 진행된다. 36TB 대신 샘플 데이터(수 GB)로 기능 검증을 하고, Airflow Databricks Operator 연결 방식은 설정 데모로 대체한다. 실제 파이프라인 전환이 아닌 전환 가능성 시연이다.

---

### C. 성능 비교

**목적**
기존 카카오페이가 사용 중인 Impala, Trino(Starburst), StarRocks의 쿼리 성능과 Databricks SQL/Photon을 동일 쿼리 기준으로 비교하여 마이그레이션 시 성능 변화를 정량적으로 확인한다.

**왜 그대로 구현이 안 되는가**
- 기존 시스템(Impala, Starburst, StarRocks)에 접근하여 동일 조건으로 측정하는 것이 불가능하다.
- 기존 수치는 카카오페이가 내부에서 직접 측정하여 제공해야만 비교 가능하다.
- 동일 데이터셋, 동일 쿼리, 동일 클러스터 규모로 대조군을 구성하는 것은 SE 팀 단독으로 할 수 없다.

**실제 구현**
Databricks 측 성능 수치만 측정하고, 카카오페이가 제공한 기존 시스템 수치와 단순 병렬 비교표를 작성한다. TPC-H 1TB 벤치마크는 공개 데이터셋으로 독립 측정이 가능하다. Photon On/Off 비교와 동시 사용자 성능 테스트는 Databricks 내에서 자체 실행 가능하다. 단, 기존 시스템 수치가 카카오페이 제공 기준이므로 측정 조건 차이에 따른 신뢰도 이슈가 남는다.

---

### D. SQL Warehouse / BI 연동

**목적**
카카오페이가 현재 Impala/Starburst에 JDBC로 연결하여 사용 중인 MicroStrategy(MSTR) BI 도구를 Databricks SQL Warehouse로 연결 대상만 변경하여 기존 대시보드/큐브 쿼리가 그대로 동작하는지 확인한다.

**왜 그대로 구현이 안 되는가**
- MSTR은 카카오페이 내부 라이선스 환경에서만 실행된다. SE 팀이 MSTR 클라이언트를 보유하거나 접근할 수 없다.
- MSTR 큐브는 카카오페이 내부 스키마 기반으로 구성되어 있어 외부에서 재현 불가.
- 실제 JDBC 연결 변경 작업은 카카오페이 MSTR 관리자가 직접 수행해야 한다.

**실제 구현**
Databricks SQL Warehouse JDBC 엔드포인트 설정, Service Principal 생성, 토큰 발급, Unity Catalog 연결 설정 절차를 문서화하고 데모로 보여주는 수준에서 진행된다. 실제 MSTR 큐브 쿼리 테스트는 카카오페이 측이 이 가이드를 따라 직접 수행해야 완성된다.

---

### E. 실시간 조회 / 서빙 (100ms)

**목적**
카카오페이가 StarRocks에서 경험한 100ms 미만 응답 시간을 Databricks SQL Warehouse로 달성할 수 있는지 검증한다. 동시 접속 100명 이상 환경에서의 안정성도 포함된다.

**왜 그대로 구현이 안 되는가**
- Databricks SQL Warehouse는 분석/대화형 SQL에 최적화된 엔진으로, StarRocks와 같은 초저지연 OLAP 서빙 영역의 아키텍처가 아니다.
- StarRocks는 인메모리 처리 기반 OLAP 전용 엔진이며, Databricks SQL Warehouse는 이 영역에서 구조적으로 경쟁 대상이 아니다.
- 100ms는 사람이 인지하기 어려운 수준으로, 일반 분석 DB 통상 응답(2~3초)과 카테고리 자체가 다르다.

**실제 구현**
워밍업된 SQL Warehouse에서 단순 집계 쿼리의 응답 시간을 측정하여 수치를 제시한다. 달성 가능한 범위의 최솟값을 보여주되, 100ms 목표에 대해서는 1차 정리 문서에서 이미 지적했듯 목표 완화 협의가 병행되어야 한다. 이 시나리오는 Databricks SQL Warehouse가 아닌 별도 아키텍처(예: DynamoDB 서빙 레이어, ElastiCache) 조합을 제안하는 방향이 더 현실적일 수 있다.

---

### F. Delta Live Tables / Streaming Table

**목적**
DLT(Delta Live Tables) 프레임워크로 스트리밍 적재 파이프라인을 선언형으로 구성하고, Streaming Table과 Materialized View 간 동기화 성능 및 탈퇴자 삭제 후 Compaction 시 변경사항 추적 이슈를 검증한다.

**왜 그대로 구현이 안 되는가**
- 실제 Kafka 스트림 연결이 없으면 진정한 의미의 스트리밍 파이프라인 검증이 불가능하다.
- 탈퇴자 삭제와 Compaction 이슈는 동시 스트리밍이 진행 중인 환경에서만 재현된다.

**실제 구현**
S3 파일 기반 Auto Loader를 소스로 하는 DLT 파이프라인을 구성한다. Auto Loader가 S3에 새로 올라오는 파일을 감지하여 처리하는 방식으로 스트리밍을 시뮬레이션할 수 있어, DLT 파이프라인 구조와 Materialized View 동기화 기능 자체는 실제로 시연 가능하다. 동시 삭제와의 충돌 시나리오는 재현 불가.

---

### G. 스키마 변경

**목적**
7TB 규모 테이블에 대해 서비스 중단 없이 컬럼 추가/삭제/타입 변경을 1시간 이내에 완료할 수 있는지 검증한다. 기존 Pinot에서 동일 작업에 24시간이 소요된 사례와 비교하는 것이 목적이다.

**왜 그대로 구현이 안 되는가**
- 7TB 실제 데이터를 9일 PoC 환경에서 준비하는 것은 비용·시간 양면에서 비현실적이다.
- 실데이터 없이 소규모로 테스트하면 I/O 패턴이 달라 실제 소요 시간 예측의 신뢰도가 낮아진다.

**실제 구현**
수십 GB 수준의 샘플 데이터로 Delta Lake의 스키마 변경 DDL 기능을 시연하고, 실행 시간을 측정하여 7TB 기준 추정치를 제시한다. Delta Lake의 스키마 변경 자체가 메타데이터 조작으로 처리되어 데이터 재작성이 불필요하다는 구조적 특성을 설명하는 것이 더 설득력 있는 접근이다.

---

### H. CDC 처리

**목적**
MySQL binlog를 Debezium이 캡처하여 내부 도구(Minecraft)를 거쳐 Kafka로 전달하는 카카오페이 CDC 파이프라인의 Consumer를 Databricks DLT로 교체하고, Insert/Update/Delete 순서 보장 및 Schema Evolution 자동 처리를 검증한다.

**왜 그대로 구현이 안 되는가**
- MySQL, Debezium, Kafka, Minecraft(내부 CDC 도구) 모두 카카오페이 온프렘에 있으며, SE 팀이 접근하거나 수정할 수 없다.
- 실시간 CDC Consumer를 Databricks로 교체하려면 카카오페이 내부 파이프라인을 수정해야 한다.
- Kafka Consumer 그룹 등록 자체가 온프렘 Kafka 접근을 전제로 한다.

**실제 구현**
카카오페이가 S3에 올려준 CDC 이벤트 파일(Insert/Update/Delete 이벤트가 포함된 JSON/Avro)을 DLT로 읽어 Delta 테이블에 Merge 처리하는 배치 replay 방식으로 진행한다. 실시간 CDC가 아니라 파일 기반 처리이므로, 순서 보장과 Exactly-Once는 구조적으로 재현이 제한된다.

---

### I. 탈퇴자 삭제 / 컴플라이언스

**목적**
GDPR 기준으로 탈퇴자 개인정보를 84TB 데이터에서 12만 건, 48시간 이내에 삭제하면서 동시에 초당 4.5만 건의 실시간 스트리밍 수집이 진행되는 상황에서 행 수준 동시성을 검증한다. PoC 전체에서 도입 판단의 핵심 시나리오다.

**왜 그대로 구현이 안 되는가**
- 84TB 데이터를 PoC 환경에 준비하는 것은 비용·시간 양면에서 비현실적이다.
- 동시 스트리밍이 없으면 충돌 검증 자체가 불가능하다. 이 시나리오의 핵심은 삭제 성능이 아니라 삭제와 스트리밍의 동시 충돌 여부인데, 스트리밍 소스가 없으면 조건 자체가 성립하지 않는다.
- 12만 건 탈퇴자 PK는 실제 개인정보이므로, 마스킹 처리된 데이터로 대체하더라도 실제 분포와 동일한 테스트 조건 구성이 어렵다.

**실제 구현**
수십 GB 수준의 샘플 데이터에 Deletion Vectors를 적용한 삭제 기능을 시연하고, Liquid Clustering으로 탈퇴자 PK 기준 파일을 집중시켜 삭제 범위를 좁히는 최적화 기법을 보여준다. 행 수준 동시성은 Notebook 내 병렬 셀 실행으로 제한적으로 재현한다. PoC 가장 핵심 시나리오임에도 불구하고 현실적으로 가장 불완전하게 검증될 수밖에 없는 항목이다.

---

### J. 보안 / 권한 / 컴플라이언스

**목적**
Unity Catalog 기반으로 분석용·식별용 카탈로그를 분리하고, Row Filtering, Column Masking, Audit Log를 구성한다. QueryPie 연동, 샤카(내부 사전 승인 시스템) API 연동, Apache Ranger 정책의 Unity Catalog 대체 가능성을 검증한다.

**왜 그대로 구현이 안 되는가**
- QueryPie와 샤카는 카카오페이 내부 시스템이며, SE 팀이 접근하거나 연동 설정을 할 수 없다.
- Apache Ranger 정책을 Unity Catalog로 1:1 매핑하려면 기존 Ranger 정책 목록을 카카오페이가 제공해야 한다.

**실제 구현**
Unity Catalog Row Filtering, Column Masking, 그룹별 권한 분리, Audit Log(System Tables) 기능을 데모 데이터로 시연한다. QueryPie/샤카 연동은 아키텍처 설계 문서 및 연동 가이드 제공으로 대체한다. Apache Ranger 대비 Unity Catalog의 기능 커버리지 비교는 문서로 제공 가능하다.

---

### K. 인프라 / 클라우드 구성

**목적**
Databricks Workspace의 AWS 클라우드 구성(S3 버킷 분리, Gateway Endpoint)을 완성하고, Keycloak → AWS SSO → Databricks SSO 체인을 구성한다. 온프렘 Hadoop Kerberos 인증을 통해 HDFS에 접근하고, Hive Metastore를 External로 등록한다.

**왜 그대로 구현이 안 되는가**
- Keycloak은 카카오페이 내부 SSO 서버이므로 외부에서 직접 연동 설정 불가.
- Kerberos 인증은 카카오페이 내부 KDC 서버에 접근이 전제되어야 하므로 불가.
- Hive Metastore External 등록도 온프렘 Metastore 주소 접근이 필요하다.

**실제 구현**
Databricks Workspace + Unity Catalog + S3 버킷 구성(DBFS, UC, External 분리)은 완전히 구현 가능하다. Keycloak SSO 체인은 설정 가이드 문서로 대체하고, Kerberos/HDFS 연동은 데모 불가 항목으로 분류한다. 이 부분은 PoC 이후 실제 마이그레이션 단계에서 카카오페이 내부 팀과 함께 진행해야 하는 항목임을 명시한다.

---

### L. 데이터 이관

**목적**
DistCp를 사용하여 카카오페이 HDFS 데이터를 S3로 직접 복제하고, 네트워크 대역폭 병목과 QoS 영향도를 측정한다. 이후 Databricks에서 S3 데이터를 Delta 포맷으로 변환한다.

**왜 그대로 구현이 안 되는가**
- DistCp는 HDFS 클러스터에서 실행하는 도구로, 카카오페이 온프렘에서만 실행 가능하다.
- HDFS 접근 권한 없이 SE 팀이 이관 속도나 대역폭 병목을 직접 측정할 수 없다.
- 실제 이관은 카카오페이가 내부에서 실행해야 하며, SE 팀은 결과물(S3에 올라온 파일)을 받아서 작업한다.

**실제 구현**
카카오페이가 S3에 올려준 데이터를 기준으로 Parquet → Delta 변환 작업만 수행한다. DistCp 이관 자체의 성능 측정은 불가하며, 변환 소요 시간과 파일 크기 변화만 측정 가능하다. DistCp 실행 가이드는 문서로 제공한다.

---

### M. 데이터 아키텍처 / 저장 포맷

**목적**
Delta Lake Native, Managed Iceberg, External Iceberg, UniForm, Parquet 간 읽기/쓰기 성능을 비교하고, Liquid Clustering, Deletion Vectors, 행 수준 동시성 기능을 실측한다.

**왜 그대로 구현이 안 되는가**
- 특별한 외부 의존성이 없는 시나리오로, 한계 사항이 거의 없다.
- 단, 실제 카카오페이 운영 데이터 볼륨(수백 TB)으로 테스트할 수 없어 대규모 환경에서의 성능 외삽 신뢰도 이슈는 있다.

**실제 구현**
9일 PoC 내에서 가장 완성도 있게 구현 가능한 시나리오다. 제공된 샘플 데이터로 포맷별 성능 비교, Liquid Clustering 효과 측정, Deletion Vectors 적용 전후 삭제 성능 비교를 실제로 실행하고 수치를 제시할 수 있다.

---

### N. 비용 / TCO 최적화

**목적**
Databricks가 단순히 빠른 것이 아니라 총비용(TCO) 기준으로도 온프렘 대비 유리한지 검증한다. Spot Instance, Serverless vs Classic SQL Warehouse, S3 Lifecycle 정책, OPTIMIZE/VACUUM 전략을 포함한다.

**왜 그대로 구현이 안 되는가**
- Serverless SQL Warehouse는 CSP 안전성 평가가 미완료 상태로 금융사 사용 불가. 비용 비교의 핵심 항목이 현재 사용 불가한 상태다.
- 실제 운영 워크로드 없이 PoC 환경에서 측정한 비용은 실제 운영 비용과 다를 수 있다.
- 카카오페이의 현재 온프렘 TCO 수치는 카카오페이가 제공해야 비교 가능하다.

**실제 구현**
Classic SQL Warehouse 기준 DBU 소비량을 측정하고, Spot Instance 설정 방법을 시연한다. Serverless 비용은 Databricks 공식 자료와 레퍼런스 사례로 대체한다. S3 Lifecycle 정책(Standard-IA, Glacier 전환)과 VACUUM 전략은 설계 문서로 제공한다.

---

### O. 모니터링 / 관제

**목적**
Databricks를 카카오페이 사내 중앙 관제 체계(Grafana, CloudWatch, Prometheus, Slack)에 연동하고, Unity Catalog Lineage와 QueryPie Audit Log를 활성화한다.

**왜 그대로 구현이 안 되는가**
- 카카오페이 내부 Grafana 인스턴스, Slack 워크스페이스, Prometheus 서버에 접근 불가.
- QueryPie 연동은 카카오페이 내부 QueryPie 서버가 있어야 테스트 가능하다.

**실제 구현**
UC System Tables(쿼리 이력, 비용, Audit Log) 조회 데모, Workflow 실패 시 이메일/Webhook 알람 설정, Unity Catalog Lineage 자동 추적 기능을 Databricks 내에서 시연한다. Grafana/CloudWatch/Prometheus 연동은 아키텍처 설계 문서와 연동 가이드로 대체한다.

---

### P-1. ML 파이프라인 이관 (BM Index)

**목적**
카카오페이 내부 ML 모델인 BM Index 2개의 학습(training)/추론(inference) 파이프라인을 Databricks로 이관하고, 2,000만 유저 × 200 feature 규모의 배치 추론을 MLflow 기반으로 운영할 수 있는지 확인한다.

**왜 그대로 구현이 안 되는가**
- BM Index 모델 파일(Pickle/H5)과 학습 데이터가 카카오페이 내부에 있으며, S3 업로드 여부가 Action Item #4로 남아있어 미확정이다.
- 2,000만 유저 전체 배치 추론은 9일 내 시간과 비용 양면에서 비현실적이다.
- 실제 학습 파이프라인 재현에는 카카오페이 내부 데이터 파이프라인 이해와 코드가 필요하다.

**실제 구현**
카카오페이가 S3에 올려준 모델 파일을 MLflow Model Registry에 등록하고, 소규모 샘플 데이터로 추론을 실행하는 데모 수준으로 진행한다. Airflow → Databricks Workflow 연동 방식은 설정 데모로 보여준다. 2,000만 유저 전체 규모 배치 추론은 아키텍처 설계와 비용 추정 문서로 대체한다.

---

### P-2. 신규 LAL PoC

**목적**
Look-Alike 모델을 Databricks에서 구성하고, 광고 Feature Store, 임베딩 적재, Vector Search, CTR Prediction 실시간 서빙(100ms 이내)까지 운영 가능한지 확인한다.

**왜 그대로 구현이 안 되는가**
- 실제 유저 데이터 없이 LAL 모델 자체를 의미 있게 구성할 수 없다.
- Feature Store 구성, 임베딩 적재, Vector Search까지 포함하면 PoC가 아닌 별도 구축 프로젝트 수준의 공수가 필요하다.
- CTR Prediction 100ms 실시간 서빙은 E 시나리오와 동일한 이유로 Databricks SQL Warehouse로 달성이 어렵다.

**실제 구현**
Databricks Feature Store, Mosaic AI Vector Search 기능을 데모 데이터로 시연하는 수준에서 진행한다. 실제 LAL 모델 학습과 2,000만 유저 타겟 추출, CTR Prediction 실시간 서빙은 PoC 범위를 초과하며, 후속 프로젝트로 분리하는 것이 현실적이다.

---

## 종합 요약

### 구현 가능성 분류

| 구분 | 시나리오 |
|:---|:---|
| **실제 구현 가능** | A-2 (Iceberg→Delta), M (포맷 비교·Liquid Clustering·Deletion Vectors), J (UC 권한·마스킹), K (Workspace·S3 구성 부분) |
| **기능 데모 수준** | B (배치 ETL 샘플), C (Databricks 측 성능만), F (Auto Loader DLT), G (소규모 DDL), N (Classic 비용 측정), O (UC System Tables), P-1 (MLflow 모델 등록) |
| **시뮬레이션/대체** | A-1 (S3 replay), A-3 (추출 파일 변환), H (CDC 파일 replay), I (소규모 삭제 데모) |
| **구현 사실상 불가** | D (MSTR 큐브), E (100ms), K (Keycloak SSO·Kerberos), L (DistCp 이관 속도), P-2 (LAL 전체) |

### 핵심 메시지

9일, SE 단독, S3 덤프 데이터 조건에서 이 PoC는 **Databricks 기능을 보여주는 데모**에 가깝다.
카카오페이가 가장 검증하고 싶은 핵심 시나리오(탈퇴자 삭제 + 동시 스트리밍 충돌, 실시간 CDC, 100ms 서빙)는 현실적인 조건에서 완전한 검증이 불가능하다.
PoC 킥오프 전에 **"실제로 검증되는 항목"과 "데모/문서로 대체되는 항목"**을 카카오페이와 명시적으로 합의해두지 않으면, PoC 결과에 대한 신뢰도 이슈와 기대치 괴리가 발생할 가능성이 높다.
