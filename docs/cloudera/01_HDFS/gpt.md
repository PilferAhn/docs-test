# HDFS (GPT 답변)

> 출처: ChatGPT 답변 원문

## Cloudera에서의 역할

HDFS는 Hadoop의 핵심 분산 파일 시스템입니다. Cloudera 문서에서도 **대용량 데이터를 commodity 서버 클러스터에 저장하는 확장 가능하고 신뢰성 있는 파일 시스템**이라고 설명하며, Hadoop에서 **저장 계층**을 담당합니다. YARN이 리소스 관리를 하고 HDFS가 저장을 맡는 구조입니다.

### 실제 역할 상세
- 파일 블록을 여러 노드에 분산 저장
- 복제(replication)를 통해 장애 허용성 제공
- Hive, Impala, Spark, MapReduce 같은 엔진들이 데이터를 읽는 기본 저장소 역할
- 운영자는 NameNode, DataNode, 용량, 블록 배치, 밸런싱, 스냅샷, 권한 등을 직접 관리

## Databricks 대응

**HDFS에 해당하는 것은 Databricks 자체가 아니라 클라우드 오브젝트 스토리지**입니다.

- AWS면 **S3**
- Azure면 **ADLS**
- GCP면 **GCS**

Databricks는 그 위에 **Delta Lake**와 **Unity Catalog external location / managed storage**를 얹습니다.

### 실무 매핑
- HDFS의 "물리 저장소" 역할 → **S3/ADLS/GCS**
- HDFS 위 메타/트랜잭션 보강 → **Delta Lake**
- HDFS 권한/접근 거버넌스 일부 → **Unity Catalog external locations / volumes / grants**

## 한 줄 매핑

**HDFS ≈ Cloud Object Storage + Delta Lake + Unity Catalog external locations**

> 이건 Databricks 전환에서 가장 중요한 개념입니다.
