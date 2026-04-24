# POC.xlsx 원본 분석 내용

> 원본 텍스트 그대로 보존

---

네. 이번에는 **POC.xlsx 전체 8개 시트**를 실제로 열어서 확인했습니다.

확인된 시트는 아래입니다.

1. **PoC 시나리오**
2. **쿼리 성능 테스트**
3. **1. PoC 일정계획**
4. **2. 데이터엔지니어링**
5. **3. SQL 웨어하우스**
6. **4.DSMLOps**
7. **5.데이터분석**
8. **DE사용현황**

핵심 결론부터 말하면, 이 파일은 **Cloudera/온프렘/Hadoop 기반 데이터 플랫폼을 Databricks Lakehouse로 전환할 수 있는지 검증하기 위한 PoC 시나리오 모음집**입니다.
다만 일부 시트는 상세 내용이 거의 비어 있고, 가장 중요한 내용은 **"PoC 시나리오" 시트**에 집중되어 있습니다.

---

## 1. 전체 구조 요약

### 현재 AS-IS 자산

`DE사용현황` 시트 기준 현재 대상 자산은 다음입니다.

* Cloudera

  * Hive Metastore
  * Hive Table
  * Kudu Table
  * Impala
* Iceberg / Tiara

  * HDFS External Table
  * Hive Metastore
* MSTR

  * BI 연동
* Airflow
* DataHub

즉, 현재는 **Cloudera + Hadoop + Hive/Kudu/Impala + Airflow + BI 도구** 중심 구조입니다.

---

## 2. 이 PoC의 목적

쉽게 말하면 다음을 확인하는 프로젝트입니다.

> "현재 Cloudera에서 돌고 있는 데이터 적재, ETL, 분석, BI, ML, 보안, 운영 체계를 Databricks로 옮겨도 문제없이 돌아가는가?"

검증 범위는 꽤 넓습니다.

* 데이터 적재
* 실시간 스트리밍
* CDC 처리
* 배치 ETL
* SQL 성능
* BI 연동
* 권한/보안
* 컴플라이언스
* Airflow 연동
* Delta Lake 전환
* ML/MLOps
* GPU 학습
* Feature Store
* 실시간 모델 서빙
* 비용/TCO
* 모니터링/Grafana
* Unity Catalog 기반 거버넌스

---

## 3. 가장 중요한 시트: PoC 시나리오

이 시트가 사실상 메인입니다.

초반에는 간단한 이관 후보가 있고, 뒤쪽으로 갈수록 매우 구체적인 검증 시나리오가 나옵니다.

---

# 주요 PoC 시나리오 정리

## A. 데이터 적재 / 마이그레이션

### 1) Kafka → Delta Lake

티아라 행동로그를 Kafka에서 받아 Databricks Delta Lake에 실시간 적재하는 시나리오입니다.

검증 내용:

* 초당 4.5만 건 처리
* pay_account_id 실시간 보강
* Exactly-Once 보장
* CDC → Kafka → Structured Streaming → Delta Lake 전체 지연시간 측정
* 장애 복구 방안
* Upsert / Merge 검증
* Small File 문제 확인
* Optimize / Compaction 주기 검토
* 탈퇴자 삭제 쿼리 성능 영향도 확인

데이터 규모:

* 티아라 230GB/day
* 75개 컬럼
* 1개월 약 7TB

성공 기준:

* 기존 NiFi 또는 Flink와 동등 이상

---

### 2) Iceberg → Parquet → Delta

기존 Iceberg 데이터를 Spark로 읽어서 Parquet/Delta로 전환하는 흐름입니다.

대상 예시:

* tiara_complete_log_raw
* tiara_ns

데이터 범위:

* 10/20 ~ 10/26

---

### 3) Kudu → Delta

Kudu 테이블을 Spark Connector로 읽어 Delta로 전환하는 시나리오입니다.

대상 예시:

* an005d04
* bp501d01

데이터 범위:

* an005d04: 10/01 ~ 10/26
* bp501d01: 2025/01/01 ~ 2025/10/26

핵심은 **Kudu + Impala 기반 조회/처리를 Delta + Databricks SQL로 대체 가능한가**입니다.

---

## B. ETL / 배치 파이프라인 전환

현재 Hive, Kudu, Tiara 기반 ETL을 Databricks로 옮기는 내용입니다.

검증 항목:

* 연결 및 추출
* 변환 및 가공
* 배치 파이프라인 전환
* Airflow Databricks Operator 호환성
* Databricks Workflow 사용성
* Databricks Lakeflow / SDP 검토
* 데이터 품질 로깅 및 모니터링

특히 중요한 시나리오는:

> 티아라 DW 배치 파이프라인 전환 검증

기존 병목으로 적힌 내용:

* Impala row_number 병목
* Aggregation 병목
* Heavy UDF
* JSON Parsing 작업

데이터 범위:

* 최근 한 달
* 티아라, 마이데이터, 결제, 머니
* 총 데이터 사이즈 약 36TB
* 총 테이블 수 45개

---

## C. 성능 비교

성능 비교는 여러 관점으로 나옵니다.

### 비교 대상

* 기존 Cloudera / Impala / Trino / Ceph 구조
* Databricks SQL
* Databricks Photon
* Delta Lake
* Managed Iceberg
* External Iceberg
* StarRocks

### 주요 테스트

* Top 5 쿼리 성능 비교
* 배치 Top 5 쿼리 성능 비교
* TPC-H 1TB 기반 성능 비교
* Trino vs Databricks 비교
* Photon On/Off 비교
* Classic SQL Warehouse vs Serverless SQL Warehouse 비교
* 동시 사용자 쿼리 성능
* Auto-scaling 성능
* 인스턴스 타입별 성능

`쿼리 성능 테스트` 시트는 현재 헤더만 있습니다.

컬럼:

* DML
* SQL warehouse
* DBX 성능
* 기존 성능

즉, 성능 결과를 채우기 위한 템플릿 상태입니다.

---

## D. SQL Warehouse / BI 연동

MSTR 같은 BI 도구와 Databricks SQL Warehouse 연동을 검증합니다.

검증 항목:

* Service Principal 생성
* SP 토큰 생성
* SP 권한 관리
* Unity Catalog 연결
* 카탈로그/스키마/테이블 조회
* 큐브 쿼리 성능
* Databricks SQL 사용 시 서버 리소스 모니터링
* 집계 쿼리 수행 성능

중요 포인트는:

> 기존 MSTR BI 사용자가 Databricks SQL Warehouse를 통해 기존처럼 안정적으로 조회할 수 있는가?

---

## E. 실시간 조회 / 서빙

Databricks SQL Warehouse를 실시간 서빙 용도로 사용할 수 있는지도 봅니다.

검증 항목:

* API 응답 속도
* 콜드 스타트 시간
* 동시 접속 100명 이상
* 실시간 적재 중 조회 성능
* 조회 실패율
* 수집 지연 여부

비교 대상으로 StarRocks도 언급되어 있습니다.

특히 목표로 적힌 내용:

* StarRocks는 100ms 미만 목표
* Databricks SQL Warehouse도 비교 대상
* 실시간 적재 중 조회 응답 시간이 기존 대비 150% 이내인지 확인

---

## F. Delta Live Tables / Streaming Table

DLT도 테스트 범위에 포함되어 있습니다.

검증 내용:

* Streaming Table 적재 성능
* Streaming Table과 Materialized View 동기화 성능
* 정합성
* 탈퇴자 삭제 / Compaction 후 변경사항 추적 이슈
* MV 재구축 시간
* 외부 Spark 적재 방식과 DLT 방식의 리소스/성능 비교

---

## G. 스키마 변경

운영 관점에서 중요한 테스트입니다.

시나리오:

> 대용량 7TB 테이블에 대해 온라인 스키마 변경이 가능한가?

검증 내용:

* 컬럼 추가
* 컬럼 삭제
* 타입 변경
* 수집 지연 없음
* 조회 영향 없음
* 무중단 처리
* DDL 완료 1시간 이내

기존 대비 문제점으로는 Pinot에서 24시간 걸린다는 언급이 있습니다.

---

## H. CDC 처리

결제 데이터 CDC가 포함되어 있습니다.

시나리오:

> MySQL binlog → Minecraft → Kafka → DLT CDC

검증 내용:

* Insert 처리
* Update 처리
* Delete 처리
* Exactly-Once 보장
* 데이터 변경 순서 보장
* Schema Evolution 자동 처리
* Kafka lag 12시간 누적 후 복구

데이터 규모:

* 결제 초당 600건
* Kafka lag 12시간 약 2,600만 건

---

## I. 탈퇴자 삭제 / 컴플라이언스

이 파일에서 매우 중요한 항목입니다.

결제 데이터 기준:

### 1개월 데이터 삭제 테스트

* 1개월 225GB
* 탈퇴자 PK 1만 건
* 삭제 중 조회 정합성 검증
* GDPR 기준 24시간 이내 삭제 완료
* MVCC 보장
* 0-byte Parquet 방어
* 실시간 수집과 삭제 동시 실행 시 충돌 검증

### 1년 데이터 삭제 테스트

* 1년 84TB
* 탈퇴자 PK 12만 건
* 삭제 완료 목표 48시간 이내
* 파티션 병렬 처리 가능 여부 확인

핵심은:

> Delta Lake에서 대용량 개인정보 삭제를 안전하고 빠르게 처리할 수 있는가?

---

## J. 보안 / 권한 / 컴플라이언스

검증 항목이 매우 구체적입니다.

### 접근 통제

* SQL Editor 접근 통제
* 식별DB 접근 차단
* 분석DB만 접근 허용
* 조회 사유 선입력
* Audit Log 기록
* Notebook Export 사후 승인
* QueryPie 연동

### 배치 승인

* Workflow 컴플라이언스
* 샤카 사전승인 API 연동
* 실패 Job 승인 관리
* Audit Log 기록

### Unity Catalog 기반 권한

* 분석용 catalog
* 식별용 catalog
* 그룹별 Read/Write 권한 분리
* Row Filtering
* Column Masking
* Apache Ranger 대체 가능성 검증

---

## K. 인프라 / 클라우드 구성

클라우드 전환 관점의 항목도 있습니다.

검증 내용:

* S3 버킷 분리

  * DBFS
  * Unity Catalog
  * External
* S3 Gateway Endpoint
* 버킷 정책
* Keycloak ↔ AWS SSO ↔ Databricks SSO 연동
* Service Principal 생성
* Workspace / Cluster 생성 권한 제어
* GitHub ↔ Databricks Git Folder 연동

온프렘 연동:

* Kerberos 연동
* Keytab을 Databricks Secrets에 등록
* Init Script로 kinit 수행
* HDFS 접근용 KDC 인증
* 온프렘 Hive Metastore / HMS External 등록
* Trino에서 Databricks UC 질의
* UniForm + Trino Iceberg Connector 검증

---

## L. 데이터 이관

HDFS에서 S3로 옮기는 테스트가 있습니다.

방식:

* DistCp를 이용한 HDFS → S3 초기 적재
* Databricks를 이용한 S3 적재 및 Delta 변환

검증 내용:

* 네트워크 대역폭 병목
* QoS 영향
* 포맷 변환 소요 시간
* 초기 마이그레이션 파이프라인 완성 여부

---

## M. 데이터 아키텍처 / 저장 포맷

다음 저장 포맷 비교가 포함되어 있습니다.

* Delta Lake Native
* Managed Iceberg
* External Iceberg
* UniForm
* Parquet
* Liquid Clustering
* 기존 Partitioning

검증 내용:

* Delta Lake vs Managed Iceberg 쓰기/읽기 성능
* Metadata 생성 오버헤드
* Databricks 단일 엔진 내 쿼리 성능
* Liquid Clustering 적용 기준
* CRUD 성능
* Deletion Vectors
* 행 수준 동시성
* 다차원 검색 성능

---

## N. 비용 / TCO 최적화

비용 관점도 꽤 잘 들어가 있습니다.

검증 항목:

* Cluster Policy
* 비용 태그 강제
* Spot Instance 활용
* Job Cluster + Spot + No Pool
* All-Purpose Cluster + Instance Pool
* Auto-scaling
* Auto-termination
* Classic SQL Warehouse vs Serverless SQL Warehouse
* Photon On/Off ROI
* S3 Standard → Standard-IA 전환
* Glacier Deep Archive
* VACUUM으로 스토리지 회수
* OPTIMIZE / Z-ORDER로 Small File 통제

핵심 질문:

> Databricks가 단순히 빠른가가 아니라, 실제 총비용이 줄어드는가?

---

## O. 모니터링 / 관제

운영 관제 항목도 포함되어 있습니다.

검증 내용:

* UC System Tables 활성화
* Billing / Audit 조회
* QueryPie 연동
* Unity Catalog Lineage 자동 추적
* Workflow 실패 시 Slack 알람
* Grafana 연동

  * Databricks SQL
  * AWS CloudWatch
  * Prometheus / JMX
  * Spark Shuffle / GC / JVM Heap 모니터링

즉, Databricks를 사내 중앙 관제 체계에 붙일 수 있는지 검증합니다.

---

## P. DS / MLOps

`4.DSMLOps` 시트와 `PoC 시나리오` 후반부에 상세히 있습니다.

### 기존 ML Training / Inference 파이프라인 PoC

목적:

> BM Index 모델 2개의 training/inference 파이프라인을 Databricks로 이관 가능한지 확인

데이터 규모:

* 2,000만 유저
* 약 200개 feature
* 2개 모델

테스트 케이스:

* Training 파이프라인 테스트
* Airflow 기반 파이프라인 관리
* MLflow 기반 모니터링
* 분산 학습
* GPU 활용
* Inference 파이프라인 테스트
* 2,000만 유저 × 2개 모델 배치 추론
* 온라인/오프라인 Feature Store 구성 가능성

---

### 신규 LAL PoC

목적:

> 신규 LAL 모델 운영 가능 여부 확인

데이터 규모:

* 2,000만 유저 × n개 feature

테스트 케이스:

* 광고 Feature Store 테스트
* 임베딩 적재 지원
* Vector Search / FAISS 가능성
* 지속 학습 파이프라인
* 타겟 추출 API
* 10만 유저 → 100만 유저 확장
* 실제로는 1,000만+ 대상 검색/추론 가능성 확인
* CTR Prediction 실시간 서빙
* 100ms 이내 응답 가능성 검토

---

## 4. 각 보조 시트 요약

### 1. PoC 일정계획

현재는 템플릿 수준입니다.

컬럼:

* No.
* 구분
* 내용
* 데이터브릭스 담당자
* 고객사 담당자
* 예상 소요 기간
* 일정
* 비고

실제 일정 데이터는 거의 입력되어 있지 않습니다.

---

### 2. 데이터엔지니어링

검증 체크리스트 시트입니다.

주요 항목:

* 클러스터 생성 편의성
* 온디맨드/스팟 인스턴스
* 액세스 모드
* Graviton 활용
* HMS 연동
* 정형/반정형/스트리밍 데이터 로딩
* 파티셔닝
* Small File 문제
* 증분 적재
* History Table
* 데이터 리니지
* DML
* Upsert
* 데이터 마스킹
* 스키마 변경
* Git 연동
* 스케줄 잡
* 잡 알림
* 잡 SLA
* 잡 모니터링
* 잡 동시성
* 권한 관리
* SSO 연동

하지만 요구사항/검증결과는 대부분 비어 있습니다.

---

### 3. SQL 웨어하우스

SQL, Dashboard, Alert, Notebook 항목이 있으나 상세 요구사항은 비어 있습니다.

즉, 아직 작성 전 템플릿에 가깝습니다.

---

### 4. DSMLOps

상세도가 높은 시트입니다.

핵심 항목:

* ML 리소스 관리
* ML Runtime 환경 구성
* Feature Store 이관
* Legacy Model Import
* Kudu/Hive On-prem 연결
* 대용량 전처리
* 분산 학습
* PyTorch / XGBoost / LightGBM
* MLflow 모니터링
* Databricks Workflows
* Airflow 연동
* 대규모 Batch Inference
* Real-time Model Serving
* Model Registry
* Unity Catalog 기반 리니지
* GPU 탄력 할당
* 벤더 Lock-in 방지
* LLM / Vector DB / RAG 가능성

이 시트는 꽤 실무적으로 잘 정리되어 있습니다.

---

### 5. 데이터분석

분석가 관점의 검증 항목입니다.

주요 항목:

* Jupyter Notebook 분석 리소스 관리
* Impala SQL 문법 호환성
* Ad-hoc 분석 속도
* SQL ↔ Python/PySpark 전환 유연성
* Parquet → Delta Lake 전환
* Airflow 연동
* Delta VACUUM을 통한 임시 테이블 정리

테스트 케이스:

* 일반 워크로드: KPI 파이프라인 이관
* 복잡한 워크로드: 데이터 분석 마트 + Feature Store + 대규모 모델 Inference

---

## 5. 이 파일 기준 핵심 리스크

### 1. 범위가 너무 넓음

이 PoC는 단순 마이그레이션이 아니라:

* 데이터 플랫폼 전환
* 실시간 처리 전환
* BI 전환
* 보안/권한 전환
* ML 플랫폼 전환
* 비용 최적화
* 관제 연동

까지 포함합니다.

한 번에 다 하려면 범위가 큽니다.

---

### 2. 실시간 서빙 목표가 Databricks에 부담될 수 있음

StarRocks와 비교하면서 100ms급 응답을 언급하고 있습니다.

Databricks SQL Warehouse는 분석/BI/대화형 SQL에는 강하지만, 초저지연 OLAP 서빙은 워크로드에 따라 별도 검증이 꼭 필요합니다.

---

### 3. 탈퇴자 삭제 / GDPR 시나리오가 매우 중요함

1년 84TB, 탈퇴자 12만 건 삭제는 현실적으로 무거운 테스트입니다.

성공 여부가 Delta Lake 도입 판단에 큰 영향을 줄 수 있습니다.

---

### 4. CDC + Schema Evolution + 실시간 조회를 동시에 검증해야 함

이 조합은 운영 난이도가 높습니다.

* CDC 순서 보장
* Exactly-Once
* Schema Evolution
* Merge 성능
* 실시간 조회 영향
* Small File
* Compaction

을 같이 봐야 합니다.

---

### 5. MLOps 범위도 별도 프로젝트급

BM Index, LAL, Feature Store, Vector Search, Real-time Serving까지 포함되어 있어 데이터 플랫폼 PoC와 분리해서 관리하는 것이 좋아 보입니다.

---

## 6. 제가 보는 우선순위

이 파일 기준으로 PoC는 아래 순서로 잘라서 가는 게 좋습니다.

### 1순위: 데이터 플랫폼 핵심 검증

* HDFS/Kudu/Hive/Iceberg → Delta 전환
* Kafka → Delta Streaming
* CDC
* 36TB 배치 파이프라인
* SQL 성능 비교

### 2순위: 운영/보안 검증

* Unity Catalog
* 권한/마스킹
* QueryPie
* Audit Log
* SSO
* Service Principal
* Workflow 승인

### 3순위: BI 검증

* MSTR 연결
* SQL Warehouse
* 큐브 쿼리
* 동시 사용자
* Dashboard 성능

### 4순위: TCO 검증

* Photon On/Off
* Serverless vs Classic
* Spot Instance
* Cluster Policy
* S3 Lifecycle
* OPTIMIZE/VACUUM

### 5순위: ML/MLOps 검증

* 기존 모델 이관
* Feature Store
* Batch Inference
* GPU 학습
* LAL
* Real-time Model Serving

---

## 7. 최종 요약

이 엑셀은 단순한 체크리스트가 아니라,
**Cloudera 기반 데이터 플랫폼을 Databricks로 전환하기 위한 종합 PoC 설계 초안**입니다.

가장 중요한 검증 축은 5개입니다.

1. **데이터 이관 가능성**
   Hive, Kudu, Iceberg, HDFS 데이터를 Delta/S3로 옮길 수 있는가.

2. **성능 개선 가능성**
   Impala, Trino, StarRocks 대비 Databricks SQL/Photon이 충분히 빠른가.

3. **운영 안정성**
   CDC, 실시간 적재, 스키마 변경, 탈퇴자 삭제, 장애 복구가 가능한가.

4. **거버넌스/보안**
   Unity Catalog, 권한, 마스킹, 감사 로그, QueryPie, SSO가 사내 기준을 만족하는가.

5. **AI/ML 확장성**
   기존 ML 파이프라인, Feature Store, Batch/Real-time Inference, LAL 모델까지 Databricks에서 운영 가능한가.

한 줄로 정리하면:

> 이 PoC는 "Databricks가 Cloudera의 대체재가 될 수 있는가"를 넘어서, "Databricks를 전사 데이터·AI 플랫폼으로 쓸 수 있는가"를 검증하는 자료입니다.
