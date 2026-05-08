# 지민님 Todo List — Kakao Pay PoC

> **기준 문서:**
> - `poc_overview.md` — 시나리오 전체 설계
> - `poc_reality_analysis.md` — 시나리오별 현실 구현 범위
> - `04-28_databricks_pipeline_discussion.md` — 04/28 기술 논의 Action Items
> - `requreiemtn.xlsx` — 카카오페이 요구사항 원본 (DE-01 ~ DE-59)

---

## 1. 환경 설정 (선행 필수)

> **근거:** 04/28 Action Items + 시나리오 K (인프라 / 클라우드 구성)
> **현실 범위:** Workspace + S3 구성은 완전 구현 가능. Keycloak/Kerberos는 대상 외.

- [ ] **Storage Credential 등록**
  - Databricks 워크스페이스에서 S3 접근용 IAM Role을 Storage Credential로 등록
  - Assume Role 방식 사용 시 해당 Role을 명시적으로 등록
  - (필요시 SA와 협의 또는 직접 수행)

- [ ] **External Location 등록**
  - Storage Credential과 연결하여 PoC용 S3 버킷 경로를 External Location으로 지정
  - 카카오페이가 업로드할 데이터 경로 기준으로 설정

- [ ] **IP Access List 확인**
  - 우리 회사 IP가 워크스페이스 액세스 리스트에 등록되었는지 확인 (Speaker 1 작업 완료 후)

---

## 2. COPY INTO — 초기 데이터 적재 데모

> **근거:** 04/28 Action Items + 시나리오 A-2 (Iceberg → Delta), A-3 (Kudu → Delta)
> **현실 범위:** A-2는 실제 구현 가능 (S3의 Iceberg 파일 → Delta 변환). A-3은 Kudu 추출 파일(Parquet/CSV) 기준으로 진행.

---

### 2-1. COPY INTO 개념 및 동작 원리 이해

> COPY INTO를 실행하기 전에 동작 방식을 정확히 이해하고 있어야 한다.

- **COPY INTO란**
  - 지정한 S3 경로의 파일을 Delta 테이블로 적재하는 Databricks SQL 명령어
  - 대용량 초기 적재(Bulk Load)와 증분 적재(Incremental Load) 모두 지원
  - Autoloader와 달리 명령을 직접 실행하거나 Job으로 트리거해야 함

- **자동 체크포인트 메커니즘**
  - 한 번 처리된 파일 목록을 Delta 테이블 내부(`_delta_log` 하위)에 자동 기록
  - 동일 명령을 재실행해도 이미 처리된 파일은 건너뜀 → 중복 적재 없음
  - 체크포인트 경로를 별도로 지정할 필요 없음 (테이블에 자동 귀속)
  - 멱등성(Idempotency) 보장: 몇 번 실행해도 결과 동일

- **기본 구문 구조**
  ```sql
  COPY INTO <카탈로그>.<스키마>.<테이블명>
  FROM 's3://<버킷명>/<경로>/'
  FILEFORMAT = PARQUET
  FORMAT_OPTIONS ('mergeSchema' = 'true')
  COPY_OPTIONS ('mergeSchema' = 'true');
  ```

- **트리거 방식 이해**
  - COPY INTO 명령 자체는 트리거가 아님
  - 실제 트리거는 이 명령을 감싸는 **Databricks Job(스케줄링)** 또는 **외부 이벤트**
  - 배치 모드: Cron 스케줄로 주기 실행 (예: 매일 새벽 2시)
  - Continuous 모드: 소스 파일 감지 즉시 처리 (Auto Loader 방식)

---

### 2-2. 클러스터 스펙 산정

> 초기 적재 데이터 볼륨에 맞는 클러스터를 구성해야 한다. 04/28 논의 기준 적용.

- **메모리 산정 기준**
  - 처리 데이터 양의 **약 3배** 총 워커 메모리 확보 권장
  - 예: 100GB 데이터 → 총 300GB 워커 메모리 필요
  - 예: 64GB 워커 × 5대 = 320GB → 100GB 데이터 한 사이클 처리 가능

- **서버 구성 방향**
  - 작은 스펙 여러 대 < **큰 스펙 적은 대수** (분산 처리 효율 측면에서 유리)
  - PoC 규모(수십 GB 샘플)에서는 드라이버 1대 + 워커 2~4대 수준으로 시작

- **압축 포맷 고려**
  - Parquet: 파일 분할 읽기 가능 → CPU 코어 수 많을수록 적재 속도 향상
  - Databricks 기본 압축: **Zstandard** (원본 대비 약 1/5 압축)
  - Gzip: 분할 읽기 불가, 속도 느림 → Parquet 우선 사용

---

### 2-3. 사전 준비 체크리스트

> 노트북 실행 전 아래 항목이 모두 완료되어 있어야 한다.

- [ ] 1번(환경 설정)의 Storage Credential / External Location 등록 완료 확인
- [ ] 카카오페이가 PoC용 S3 버킷에 데이터 업로드 완료 여부 확인
- [ ] Unity Catalog에서 Bronze 테이블을 생성할 카탈로그 / 스키마 결정 및 생성
  ```sql
  CREATE CATALOG IF NOT EXISTS kpay_poc;
  CREATE SCHEMA IF NOT EXISTS kpay_poc.bronze;
  ```
- [ ] 클러스터 생성 및 External Location에 대한 접근 권한 확인
  ```sql
  -- External Location 접근 가능 여부 확인
  LIST 's3://<버킷명>/<경로>/';
  ```

---

### 2-4. COPY INTO 데모 노트북 작성

> 기본 동작을 검증하는 데모 노트북. A-2, A-3 실행 전 먼저 단순 케이스로 검증.

- [ ] **노트북 기본 구조 작성**

  ```
  [셀 1] 카탈로그 / 스키마 설정
  [셀 2] 빈 Delta 테이블 생성 (스키마 정의 또는 스키마 추론)
  [셀 3] COPY INTO 실행 (1회차)
  [셀 4] 적재 결과 확인 (행 수, 컬럼 확인)
  [셀 5] COPY INTO 재실행 (2회차) → 중복 적재 없음 검증
  [셀 6] 신규 파일 추가 후 재실행 → 증분 적재만 처리됨 검증
  ```

- [ ] **스키마 자동 추론(Schema Inference) 옵션 테스트**
  ```sql
  COPY INTO kpay_poc.bronze.sample_table
  FROM 's3://<버킷명>/sample/'
  FILEFORMAT = PARQUET
  FORMAT_OPTIONS ('inferSchema' = 'true', 'mergeSchema' = 'true');
  ```

- [ ] **적재 결과 검증 쿼리 작성**
  ```sql
  SELECT COUNT(*) FROM kpay_poc.bronze.sample_table;
  DESCRIBE HISTORY kpay_poc.bronze.sample_table;
  DESCRIBE DETAIL kpay_poc.bronze.sample_table;
  ```

---

### 2-5. 시나리오 A-2 — Iceberg → Delta 전환

> **구현 수준: 실제 구현 가능** (전체 시나리오 중 완성도 가장 높음)

- **대상 테이블**

  | 테이블명 | 데이터 범위 |
  |:---|:---|
  | `tiara_complete_log_raw` | 2024/10/20 ~ 10/26 |
  | `tiara_ns` | 2024/10/20 ~ 10/26 |

- [ ] **Iceberg 파일 읽기 확인**
  ```python
  df = spark.read.format("iceberg") \
      .load("s3://<버킷명>/iceberg/tiara_complete_log_raw/")
  df.printSchema()
  df.count()
  ```

- [ ] **Delta 테이블로 변환 및 저장**
  ```python
  df.write \
      .format("delta") \
      .mode("overwrite") \
      .saveAsTable("kpay_poc.bronze.tiara_complete_log_raw")
  ```

- [ ] **측정 항목 기록** (변환 소요 시간, 원본 vs Delta 파일 크기, 파티션 구조 변화)
- [ ] **tiara_ns 동일 방식으로 반복 실행**

---

### 2-6. 시나리오 A-3 — Kudu → Delta 전환

> **구현 수준: 시뮬레이션** (Kudu 직접 연결 불가 → 추출 파일 기반 진행)

- **대상 테이블**

  | 테이블명 | 데이터 범위 |
  |:---|:---|
  | `an005d04` | 2024/10/01 ~ 10/26 |
  | `bp501d01` | 2025/01/01 ~ 10/26 |

- [ ] **S3 파일 확인 및 포맷 파악**
  ```sql
  LIST 's3://<버킷명>/kudu/an005d04/';
  ```

- [ ] **COPY INTO로 Bronze 테이블 생성 (Parquet 기준)**
  ```sql
  COPY INTO kpay_poc.bronze.an005d04
  FROM 's3://<버킷명>/kudu/an005d04/'
  FILEFORMAT = PARQUET
  FORMAT_OPTIONS ('mergeSchema' = 'true')
  COPY_OPTIONS ('mergeSchema' = 'true');
  ```

- [ ] **bp501d01 동일 방식으로 반복 실행**
- [ ] **한계 사항 노트북 상단 주석으로 명시** (Kudu 실시간 CRUD 특성은 검증 불가)

---

### 2-7. 스케줄링 잡 구성

- [ ] **Databricks Job 생성** (Notebook Task, Job Cluster, Cron 스케줄)
- [ ] **Job 실행 후 확인** (처리 파일 수, 2회차 `0 files copied` 확인, 실패 알림 설정)
- [ ] **증분 적재 시나리오 시연** (신규 파일 추가 후 2회차 실행)

---

## 3. SDP(Declarative Pipelines) — 데이터 변환 및 품질 관리 실습

> **근거:** 04/28 Action Items + 시나리오 B (ETL/배치 파이프라인), 시나리오 F (DLT/Streaming Table)
> **현실 범위:** 시나리오 B는 데모 수준 (샘플 SQL 재작성). 시나리오 F는 Auto Loader → DLT 파이프라인 구성 가능.

- [ ] **SDP 파이프라인 초기 구성**
  - Bronze → Silver 변환 파이프라인 작성 (Python 또는 SQL)
  - 배치 모드 / Continuous 모드 차이 확인

- [ ] **Expectation(데이터 품질 규칙) 설정**
  - SQL/Python으로 데이터 품질 조건 정의 (drop / fail 처리 방식 포함)
  - `dp.expect_all` 등 Databricks 전용 함수 활용 확인

- [ ] **Auto Loader → DLT 파이프라인 구성 (시나리오 F 대응)**
  - S3 신규 파일 감지 → DLT 처리 흐름 구성
  - Materialized View 동기화 기능 시연 (정적 데이터 기준)

- [ ] **배치 ETL 샘플 노트북 작성 (시나리오 B 대응)**
  - 카카오페이가 제공한 대표 SQL을 Databricks Notebook으로 재작성
  - 샘플 데이터(수 GB) 기준 실행

- [ ] **SDP MV 동기화 중 스키마 변경 엣지 케이스 검증 (시나리오 DE-48)**
  - MV 동기화 진행 중 컬럼 추가/삭제 발생 시 동작 확인
  - MV 재구축 시간 측정 (SLA: 24시간 이내)

---

## 4. [NEW] 결제 데이터 Wide Table 적재 (시나리오 A-1-B)

> **근거:** DE-29, DE-30 (xlsx)
> **현실 범위:** 실데이터 PoC — 카카오페이 결제 데이터 제공 시 실제 구현 가능

- **데이터 규모:** 600건/초, 10KB/건, 270컬럼, 1개월 225GB
- **핵심 검증:** Wide Table 환경에서 Compaction 지연 없이 30분 이내 완료 가능한가

- [ ] **Liquid Clustering 설정 및 적재 파이프라인 구성**
  - 결제 데이터 테이블에 `CLUSTER BY (결제 PK 또는 날짜 컬럼)` 적용
  - Predictive Optimize 활성화 → 별도 수동 Compaction 없이 자동 처리 확인

- [ ] **측정 항목 기록**
  - 초당 처리 건수 (목표: 600건/초 이상)
  - Compaction 완료 시간 (목표: 30분 이내)
  - Wide Table(270컬럼) 환경에서 파일 사이즈 분포 확인

- [ ] **Liquid Clustering vs 기존 Partitioning 비교** (DE-56과 연계)
  - 동일 데이터셋 기준 CRUD 성능 및 Data Skipping 효과 측정

---

## 5. [NEW] Delta Lake 조회 성능 검증 (시나리오 A-1 조회)

> **근거:** DE-24, DE-25, DE-26 (xlsx)
> **현실 범위:** 실데이터 PoC — 티아라 1개월 7TB 기준

- [ ] **기본 조회 쿼리 성능 측정**
  - 개인 최근 100건 조회
  - 특정 서비스 접근 유저 모수 추출
  - 성공 기준: **Trino 대비 30% 이상 개선** (카카오페이가 Trino 수치 제공 필요)

- [ ] **캐시 히트 효과 측정**
  - 동일 쿼리 반복 실행 시 캐시 히트율 확인
  - 데이터 변경(적재/삭제) 후 캐시 무효화 시나리오 정의 및 테스트

- [ ] **Variant Data Type 쿼리 성능 검증** ← 기존 Impala/Trino 미지원 기능
  - JSON 컬럼 그대로 저장 후 Variant 타입으로 분석 쿼리 실행
  - 기존 JSON 파싱 방식 대비 쿼리 성능 비교
  - 사전 준비: 카카오페이와 전환 대상 JSON 스키마 합의 필요

---

## 6. [NEW] 메달리온 아키텍처 + Asset Bundles (시나리오 B-2)

> **근거:** DE-15, DE-16, DE-17, DE-18 (xlsx)
> **현실 범위:** 실제 구현 가능 — 외부 의존성 없음. GitHub Enterprise 연동은 가이드 문서로 대체.

### 6-1. SDP UI 기반 메달리온 파이프라인

- [ ] **단일 pipeline 구성 (bronze/silver/gold)**
  - 하나의 SDP pipeline 안에 bronze ST → silver MV → gold MV 정의
  - Pipelines Editor(DAG·Data Preview·Issues Panel) 사용 경험 정리
  - 산출물: ST vs MV 선택 기준 문서

- [ ] **복수 pipeline 구성 (Lakeflow Job UI)**
  - bronze/silver/gold를 각각 별도 pipeline으로 분리
  - Lakeflow Job UI에서 `pipeline_task` + `depends_on`으로 cross-pipeline 의존성 표현
  - 산출물: UI 운영 장단점 정리

### 6-2. Asset Bundles 코드 표준화 및 배포

- [ ] **Bundle 코드 구조 작성**
  - `databricks.yml` + `*.pipeline.yml` + `*.job.yml` 작성
  - `<pipeline>/<stage>/<table>.py` 3단 트리 구조
  - `root_path: ../src`로 `src/common/` 모듈 공유 구조 구성
  - 산출물: Bundle 코드화 장단점 정리

- [ ] **Bundle 배포·롤백·환경 변수 분기 검증**
  - `databricks bundle deploy` 일괄 배포 및 롤백 테스트
  - 환경별 변수 분기 (`dev` / `staging` / `prd`)
  - GitHub Enterprise 연동 가능 여부 → 연동 불가 시 설정 가이드 문서로 대체

---

## 7. [NEW] MySQL DB Ingestion — Lakeflow Connect (시나리오 L-2)

> **근거:** DE-59 (xlsx)
> **현실 범위:** 조건부 가능 — 카카오페이 MySQL 접근 권한 제공 시 실제 구현, 미제공 시 가이드 문서

- **데이터 규모:** 최대 트래픽 6.875 MB/s, TPS ≈ 7,040 (Parquet 환산)
- **전제 조건:** 카카오페이 측 **5월 말까지** 대상 MySQL 인스턴스·계정·테이블 정의·접근 권한 공유

- [ ] **카카오페이 MySQL 접근 권한 수신 확인**
  - 미수신 시 → Lakeflow Connect MySQL Connector 설정 가이드 문서 작성으로 대체

- [ ] **Lakeflow Connect MySQL Connector 구성** (접근 권한 수신 시)
  - 초기 스냅샷(전체 복제) + CDC(변경분 지속 수집) 파이프라인 설정
  - as-is 동등 이상 처리량 확인 (TPS 7,040 이상)
  - Lakeflow Connect 표준 옵션 검증

---

## 8. [NEW] 엣지 케이스 / 추가 검증

### 8-1. Tiara Kafka lag 3시간 시나리오 (DE-27, DE-28)

> **현실 범위:** 실데이터 PoC — Kafka lag 시뮬레이션 환경 사전 준비 필요

- [ ] **Kafka lag 시뮬레이션 환경 준비 방법 카카오페이와 협의**
  - 3시간 lag(240만 건) 재현 방법 합의 (실제 Consumer 중단 vs 파일 덤프 replay)

- [ ] **lag 복구 검증**
  - 복구 완료 1시간 이내 달성 여부 측정
  - Backpressure 처리 동작 확인

- [ ] **피크 트래픽 지속 성능 측정**
  - 피크 타임 트래픽 양 및 지속 시간 카카오페이 확인 필요
  - 처리량 유지율 100% 기준 충족 여부

### 8-2. Serverless vs Provisioned 분리 테스트 (DE-37, DE-38)

> **상태 업데이트:** 기존 "Serverless 사용 불가" → "콜드스타트 제외 Serverless 가능"으로 변경

- [ ] **Serverless SQL Warehouse — 콜드스타트 제외 일반 조회 성능 측정**
  - 티아라 1개월 7TB / 결제 1개월 225GB 기준
  - P90 응답 시간 측정
  - 동시 접속 100+ 부하 시뮬레이션 도구/스크립트 선정

- [ ] **Provisioned 클러스터 — 콜드스타트 시간 별도 측정**
  - 클러스터 완전 종료 후 최초 쿼리 응답까지 소요 시간 측정
  - Serverless 콜드스타트와 별도 비교 자료로 제공

---

## 9. [NEW] 사전 분석 및 문서화 (1차_정리 Action Items — SE 담당)

> **근거:** `1차_정리.md` Action Items 중 SE 담당 항목

- [ ] **[Action #1] 'Minecraft' 용어 확인**
  - CDC 맥락에서 내부 도구 'Minecraft'가 무엇인지 카카오페이에 확인

- [ ] **[Action #2] CDC 테스트용 VPN 연결 및 독립 대역폭 확보 가능 여부 문의**
  - Kafka(온프렘) → Databricks(AWS) Consumer 연결 가능 여부 확인
  - VPN 미확정 시 S3 파일 기반 replay 방식 확정

- [ ] **[Action #3] ML Feature Store·모델 모니터링 — 실구현 vs 문서 대체 협의**

- [ ] **[Action #7] Serverless CSP 평가 완료 예정 시점 Databricks 측 확인**

- [ ] **[Action #9] Starburst + Iceberg 조합 → UniForm 전환 시 영향도 분석**
  - Starburst가 UC를 External Metastore로 바라보는 구조 설계 가능 여부
  - UniForm으로 Delta/Iceberg 공존 기간 운영 방안 검토

- [ ] **[Action #10] Kudu Spark Connector 이관 성능 사전 벤치마크**
  - 파일 직접 복사 불가, Connector 경유 필수 → 병목 구간 예측

- [ ] **[Action #11] CDC lag 복구 완료 기준 정의 — 카카오페이와 협의**
  - `lag = 0` 시점 vs 데이터 정합성 검증 완료 시점 중 어느 것을 기준으로 볼지

- [ ] **[Action #12] 탈퇴자 삭제 중 스토리지 일시 2배 증가 비용 PoC 예산 반영**
  - VACUUM 실행 전 구버전 파일 유지로 스토리지 일시 증가 → 비용 계획에 포함

---

## 참고 — 현실 범위 요약

| 항목 | 구현 수준 | 비고 |
|:---|:---|:---|
| Storage Credential / External Location 설정 | **실제 구현** | 선행 필요 |
| COPY INTO 데모 노트북 | **실제 구현** | Bronze 테이블 생성 |
| A-2 Iceberg → Delta 전환 | **실제 구현** | 전체 시나리오 중 완성도 가장 높음 |
| A-3 Kudu → Delta 전환 | **시뮬레이션** | Kudu 추출 파일(Parquet/CSV) 기준, Kudu 직접 연결 없음 |
| A-1-B 결제 Wide Table 적재 | **실데이터 PoC** | 270컬럼, Liquid Clustering + Predictive Optimize |
| Delta Lake 조회 성능 검증 | **실데이터 PoC** | Trino 대비 30% 개선 기준, Variant Data Type 포함 |
| SDP Expectation 설정 | **실제 구현** | Databricks 전용 기능 포함 |
| SDP MV 동기화 + 스키마 변경 엣지 | **실데이터 PoC** | MV 재구축 SLA 24시간 이내 |
| Auto Loader → DLT 파이프라인 | **기능 데모** | 실시간 Kafka 연결 없이 S3 파일 기반 시뮬레이션 |
| 배치 ETL SQL 재작성 | **기능 데모** | 샘플 데이터 기준, 36TB 전체 처리 아님 |
| B-2 메달리온 아키텍처 + Asset Bundles | **실제 구현** | 외부 의존성 없음, GitHub Enterprise 연동은 가이드 대체 |
| L-2 MySQL Ingestion (Lakeflow Connect) | **조건부 가능** | 카카오페이 접근 권한 제공 시 실제 구현, 미제공 시 가이드 |
| Serverless 콜드스타트 제외 조회 | **실제 구현 가능** | 콜드스타트 비교는 Provisioned으로 별도 진행 |
| Kafka lag 3시간 시나리오 (Tiara) | **조건부 가능** | lag 시뮬레이션 환경 사전 협의 필요 |
