# 지민님 Todo List — Kakao Pay PoC

> **기준 문서:**
> - `poc_overview.md` — 시나리오 전체 설계
> - `poc_reality_analysis.md` — 시나리오별 현실 구현 범위
> - `04-28_databricks_pipeline_discussion.md` — 04/28 기술 논의 Action Items

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
  - Delta 테이블 생성 시 스키마를 미리 정의하지 않고 파일에서 자동 추론
  ```sql
  COPY INTO kpay_poc.bronze.sample_table
  FROM 's3://<버킷명>/sample/'
  FILEFORMAT = PARQUET
  FORMAT_OPTIONS ('inferSchema' = 'true', 'mergeSchema' = 'true');
  ```

- [ ] **적재 결과 검증 쿼리 작성**
  ```sql
  -- 적재 행 수 확인
  SELECT COUNT(*) FROM kpay_poc.bronze.sample_table;

  -- 체크포인트 이력 확인 (처리된 파일 목록)
  DESCRIBE HISTORY kpay_poc.bronze.sample_table;

  -- 파일 크기 및 파티션 구조 확인
  DESCRIBE DETAIL kpay_poc.bronze.sample_table;
  ```

---

### 2-5. 시나리오 A-2 — Iceberg → Delta 전환

> **구현 수준: 실제 구현 가능** (전체 시나리오 중 완성도 가장 높음)
> 카카오페이가 S3에 올려준 Iceberg 파일을 Spark으로 읽어 Delta로 변환한다.

- **대상 테이블**

  | 테이블명 | 데이터 범위 |
  |:---|:---|
  | `tiara_complete_log_raw` | 2024/10/20 ~ 10/26 |
  | `tiara_ns` | 2024/10/20 ~ 10/26 |

- **전환 방식**
  - COPY INTO는 Iceberg 포맷을 직접 읽지 못함
  - Spark DataFrame으로 Iceberg 파일 읽기 → Delta 포맷으로 write 하는 방식 사용

- [ ] **Iceberg 파일 읽기 확인**
  ```python
  # Iceberg 파일 읽기 (S3 경로 기준)
  df = spark.read.format("iceberg") \
      .load("s3://<버킷명>/iceberg/tiara_complete_log_raw/")

  df.printSchema()
  df.count()
  ```

- [ ] **Delta 테이블로 변환 및 저장**
  ```python
  # Delta 포맷으로 저장 (Bronze 테이블)
  df.write \
      .format("delta") \
      .mode("overwrite") \
      .saveAsTable("kpay_poc.bronze.tiara_complete_log_raw")
  ```

- [ ] **측정 항목 기록**
  - 변환 소요 시간 (초 단위)
  - 원본 Iceberg 파일 크기 vs 변환 후 Delta 파일 크기 (압축률 비교)
  - 파티션 구조 변화 확인

- [ ] **tiara_ns 동일 방식으로 반복 실행**

---

### 2-6. 시나리오 A-3 — Kudu → Delta 전환

> **구현 수준: 시뮬레이션** (Kudu 직접 연결 불가 → 추출 파일 기반으로 진행)
> 카카오페이가 Kudu 데이터를 Parquet/CSV로 추출하여 S3에 올려주면, COPY INTO로 Delta로 변환한다.

- **대상 테이블**

  | 테이블명 | 데이터 범위 |
  |:---|:---|
  | `an005d04` | 2024/10/01 ~ 10/26 |
  | `bp501d01` | 2025/01/01 ~ 10/26 |

- **전환 방식**
  - Kudu Connector를 통한 실시간 연결은 대상 외 (온프렘 직접 접근 불가)
  - 카카오페이가 Kudu → Parquet/CSV 추출 → S3 업로드 후, COPY INTO 실행

- [ ] **S3 파일 확인 및 포맷 파악**
  ```sql
  -- 카카오페이가 올려준 파일 목록 확인
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

- [ ] **CSV 포맷인 경우 옵션 추가**
  ```sql
  COPY INTO kpay_poc.bronze.an005d04
  FROM 's3://<버킷명>/kudu/an005d04/'
  FILEFORMAT = CSV
  FORMAT_OPTIONS (
    'header' = 'true',
    'inferSchema' = 'true',
    'delimiter' = ','
  );
  ```

- [ ] **bp501d01 동일 방식으로 반복 실행**

- [ ] **한계 사항 문서화**
  - Kudu 고유 특성(실시간 CRUD 순서 보장, 동시 업데이트 처리)은 이 방식으로 검증 불가
  - 해당 내용을 데모 노트북 상단 주석 또는 별도 설명 셀로 명시

---

### 2-7. 스케줄링 잡 구성

> COPY INTO는 명령 자체가 트리거가 아니므로, Job으로 감싸야 실제 파이프라인이 된다.

- [ ] **Databricks Job 생성**
  - Job 타입: Notebook Task (COPY INTO 노트북 지정)
  - 클러스터: Job Cluster (실행 시에만 생성, 완료 후 자동 종료)
  - 스케줄: Cron 표현식으로 주기 설정 (예: 매일 새벽 2시 `0 2 * * *`)

- [ ] **Job 실행 후 확인 항목**
  - Job 실행 로그에서 처리된 파일 수 및 적재 행 수 확인
  - 2회 연속 실행 시 2회차에서 `0 files copied` 출력되는지 확인 (체크포인트 정상 동작)
  - Job 실패 시 알림 설정 (이메일 또는 Webhook)

- [ ] **증분 적재 시나리오 시연**
  - 첫 번째 Job 실행 후 S3에 신규 파일 추가
  - 두 번째 Job 실행 시 신규 파일만 처리되는지 확인

---

## 3. SDP(Declarative Pipelines) — 데이터 변환 및 품질 관리 실습

> **근거:** 04/28 Action Items + 시나리오 B (ETL/배치 파이프라인), 시나리오 F (DLT/Streaming Table)
> **현실 범위:** 시나리오 B는 데모 수준 (샘플 SQL 재작성). 시나리오 F는 Auto Loader → DLT 파이프라인 구성 가능.

- [ ] **SDP 파이프라인 초기 구성**
  - Databricks UI에서 SDP 파이프라인 초기 코드 생성 (Python 또는 SQL)
  - Bronze 테이블을 소스로 Silver 테이블로 변환하는 파이프라인 작성
  - 배치 모드 / Continuous 모드 차이 확인

- [ ] **Expectation(데이터 품질 규칙) 설정**
  - SQL 또는 Python 코드로 데이터 품질 조건 정의
  - 조건 불만족 시 처리 방식 설정: drop(누락) 또는 fail(파이프라인 실패)
  - 딕셔너리(Key-Value) 형태로 규칙 구성 실습
  - `dp.expect_all` 등 Databricks 전용 함수 활용 확인

- [ ] **Auto Loader → DLT 파이프라인 구성 (시나리오 F 대응)**
  - S3에 새로 올라오는 파일을 Auto Loader가 감지 → DLT 파이프라인으로 처리하는 흐름 구성
  - Materialized View 동기화 기능 시연 (정적 데이터 기준)

- [ ] **배치 ETL 샘플 노트북 작성 (시나리오 B 대응)**
  - 카카오페이가 제공한 대표 SQL을 Databricks Notebook으로 재작성
  - 샘플 데이터(수 GB) 기준으로 실행 및 결과 확인
  - 실제 36TB 전체가 아닌 기능 검증 및 전환 가능성 시연 목적

---

## 참고 — 현실 범위 요약

| 항목 | 구현 수준 | 비고 |
|:---|:---|:---|
| Storage Credential / External Location 설정 | **실제 구현** | 선행 필요 |
| COPY INTO 데모 노트북 | **실제 구현** | Bronze 테이블 생성 |
| A-2 Iceberg → Delta 전환 | **실제 구현** | 전체 시나리오 중 완성도 가장 높음 |
| A-3 Kudu → Delta 전환 | **시뮬레이션** | Kudu 추출 파일(Parquet/CSV) 기준, Kudu 직접 연결 없음 |
| SDP Expectation 설정 | **실제 구현** | Databricks 전용 기능 포함 |
| Auto Loader → DLT 파이프라인 | **기능 데모** | 실시간 Kafka 연결 없이 S3 파일 기반 시뮬레이션 |
| 배치 ETL SQL 재작성 | **기능 데모** | 샘플 데이터 기준, 36TB 전체 처리 아님 |
