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

- [ ] **COPY INTO 데모 노트북 작성**
  - 테이블명, 파일 포맷(Parquet), S3 경로를 지정하는 기본 COPY INTO 구문 작성
  - 자동 체크포인트 동작 확인 (동일 명령 재실행 시 중복 적재 없음 검증)
  - 결과 테이블 = Bronze 테이블로 정의

- [ ] **Iceberg → Delta 전환 실행 (시나리오 A-2)**
  - 카카오페이가 S3에 올려준 Iceberg 파일(10/20~10/26 범위) 기준으로 실행
  - 대상 테이블: `tiara_complete_log_raw`, `tiara_ns`
  - Spark으로 Iceberg 파일 읽기 → Delta 변환 → 소요 시간 및 파일 크기 변화 측정

- [ ] **Kudu → Delta 전환 실행 (시나리오 A-3)**
  - 카카오페이가 Kudu 데이터를 Parquet/CSV로 추출하여 S3에 올려준 파일 기준으로 진행
  - Kudu 직접 연결(Spark Kudu Connector)은 대상 외 (온프렘 직접 접근 불가)
  - COPY INTO로 Delta 변환 후 테이블 생성 확인
  - 대상 테이블: `an005d04` (2024/10/01~10/26), `bp501d01` (2025/01/01~10/26)

- [ ] **스케줄링 잡 구성 확인**
  - COPY INTO를 실행하는 Databricks Job 생성 (배치 스케줄 또는 Continuous 트리거)

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
