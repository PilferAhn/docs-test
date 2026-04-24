# Cloudera vs Databricks 완전 정복 가이드
### — 처음 접하는 분도 이해할 수 있도록 아주 쉽게 설명합니다 —

---

## 이 문서를 읽기 전에: 두 플랫폼이 뭔가요?

**Cloudera**와 **Databricks**는 둘 다 "빅데이터를 저장하고, 분석하고, AI를 돌리는 거대한 플랫폼"입니다.

쉽게 비유하자면 이렇습니다.

> **Cloudera** = 오래된 대형 공장
> 기계 하나하나를 사람이 직접 조립하고 관리합니다.
> 각 기계(서비스)가 무슨 역할인지 눈에 보입니다.
> 운영자가 많이 필요하지만, 내부 구조를 완전히 통제할 수 있습니다.
>
> **Databricks** = 최신 스마트 공장
> 공장 안의 기계 대부분이 자동화되어 보이지 않습니다.
> 사용자는 "무엇을 만들지"만 명령하면 됩니다.
> 내부가 단순해 보이지만 실제로는 매우 강력합니다.

---

## 핵심 전제: 1:1로 딱 맞아 떨어지지 않습니다

Cloudera의 서비스들을 Databricks와 비교할 때, **정확히 1:1로 대응되는 경우는 드뭅니다.**

그 이유는 구조가 근본적으로 다르기 때문입니다.

- **Cloudera**: 개별 부품(서비스)을 사용자가 직접 보고 조합하는 방식
- **Databricks**: 여러 기능이 하나의 통합 플랫폼 안으로 합쳐져 있는 방식

어떤 Cloudera 서비스는 Databricks에서 "정확한 대응 제품"이 있고,
어떤 것은 **플랫폼 내부에 흡수**되어 보이지 않거나,
아예 **클라우드 스토리지/클라우드 설정/외부 서비스**로 대체됩니다.

---

## 전체 매핑 요약표 (한눈에 보기)

아래 표를 먼저 전체적으로 훑어보세요. 자세한 설명은 그 뒤에 이어집니다.

| Cloudera 서비스 | 역할 한 줄 요약 | Databricks 대응 |
|:---|:---|:---|
| **HDFS** | 대용량 파일을 분산 저장하는 저장소 | 클라우드 스토리지(S3/ADLS/GCS) + Delta Lake |
| **Hive Metastore** | 테이블의 설계도(스키마·위치) 보관 | Unity Catalog |
| **Hive on Tez** | SQL을 받아 실제로 실행하는 엔진 | SQL Warehouse + Spark Compute |
| **Impala** | 빠른 대화형 SQL 전용 엔진 | SQL Warehouse |
| **Kudu** | 분석에 특화된 빠른 저장 엔진 | Delta Lake |
| **Oozie** | 여러 작업을 순서대로 실행·스케줄링 | Lakeflow Jobs |
| **Ranger** | 누가 어떤 데이터에 접근할 수 있는지 권한 관리 | Unity Catalog |
| **Hue** | 웹 브라우저에서 SQL 작성하는 UI | Notebook + SQL Editor + Catalog Explorer |
| **Tez** | Hive 쿼리를 분산 실행하는 내부 엔진 | Spark 내부 실행 레이어 (직접 보이지 않음) |
| **YARN** | 클러스터 전체의 CPU/메모리 자원 배분 | Databricks Compute 관리 플레인 (내부) |
| **YARN Queue Manager** | 팀별로 자원 배분량을 조정하는 관리 도구 | Compute 정책 + SQL Warehouse 설정 |
| **ZooKeeper** | 분산 서비스들이 서로 상태를 맞추는 보조 인프라 | Databricks 내부 관리 레이어 (보이지 않음) |
| **Core Configuration** | 클러스터 공통 설정 저장소 | Databricks 컨트롤 플레인의 workspace 설정 |
| **CDP-INFRA-SOLR** | 보안 감사 로그를 검색하는 인덱스 엔진 | Unity Catalog 감사 기능 + 외부 로그 분석 도구 |
| **CDE (Data Engineering)** | Spark 기반 ETL 파이프라인 관리 | Databricks Workflows (Jobs) + Delta Live Tables |
| **CDW (Data Warehouse)** | SQL 쿼리와 BI 리포팅 서비스 | Databricks SQL |
| **CML (Machine Learning)** | 머신러닝 모델 학습·배포 환경 | Mosaic AI (MLflow 기반) |
| **CDF (DataFlow)** | 실시간 스트리밍 데이터 수집·처리 | Delta Live Tables + Spark Structured Streaming |
| **SDX (거버넌스)** | 전사 데이터 권한과 계보 통합 관리 | Unity Catalog |

---

## 서비스별 상세 설명

---

### 1. CDP-INFRA-SOLR

#### Cloudera에서 이게 뭔가요?

이름에 "SOLR"이 들어가서 일반 검색 엔진처럼 보이지만, 실제로는 **보안 감사(Audit) 전용 검색 엔진**입니다.

Cloudera에서는 **Ranger**라는 보안 서비스가 "누가 어떤 데이터에 접근했는지" 기록을 남깁니다. 이 기록(로그)이 엄청나게 많이 쌓이는데, 이것을 빠르게 검색할 수 있도록 인덱싱해 주는 것이 **CDP-INFRA-SOLR**입니다.

예를 들어 이런 질문에 답할 수 있습니다.
- "지난달에 A씨가 어떤 테이블을 읽었나?"
- "HDFS 경로에 무단 접근 시도가 있었나?"
- "보안 정책을 어긴 사건이 있었나?"

**중요:** 이 Solr는 일반 비즈니스 검색 서비스가 아닙니다. Cloudera가 직접 "커스텀 워크로드에 쓰지 말라"고 문서에 명시할 정도로, **운영자·보안팀 전용 인프라 서비스**입니다.

#### Databricks에서는 어디에 해당하나요?

Databricks에는 별도의 Solr 서비스가 없습니다. 대신 다음이 그 역할을 담당합니다.

- **Unity Catalog 내장 감사 기능**: 누가 어떤 데이터 자산에 접근했는지 기록하고 추적합니다.
- **Databricks System Tables**: 플랫폼 내부의 사용 이력, 접근 기록 등을 SQL로 조회할 수 있는 시스템 테이블이 제공됩니다.
- **외부 로그 분석 도구**: 필요에 따라 Splunk, Elastic, Azure Monitor 같은 외부 시스템을 연결합니다.

**핵심 차이**: Cloudera는 이 기능이 별도 서비스(Solr)로 눈에 보이지만, Databricks는 플랫폼 내부 기능으로 흡수되어 있습니다.

---

### 2. Core Configuration (= Core Settings)

#### Cloudera에서 이게 뭔가요?

클러스터 안의 모든 서비스가 공통으로 참조해야 하는 **설정값들을 저장하고 배포하는 서비스**입니다.

쉽게 비유하면, 회사 전체 직원이 공유하는 **사내 규정집**과 같습니다. 어떤 서비스가 새로 시작될 때 "공통 설정이 뭐더라?"를 여기서 읽어갑니다.

예전에는 이 공통 설정 배포를 HDFS가 일부 담당했는데, Core Configuration 서비스가 그 역할을 독립적으로 맡으면서 **HDFS 없이도 클러스터를 구성할 수 있게 해주는 기반 서비스**가 되었습니다.

#### Databricks에서는 어디에 해당하나요?

Databricks에는 이것과 똑같은 독립 서비스가 없습니다. 왜냐하면 이런 역할이 **플랫폼 컨트롤 플레인(Control Plane)** 안으로 자동으로 흡수되어 있기 때문입니다.

가장 가까운 개념들입니다.
- **Workspace 수준 설정**: Databricks 워크스페이스 전체에 적용되는 설정
- **Compute 정책**: 클러스터/컴퓨트 구성에 관한 규칙
- **SQL Warehouse 설정**: SQL 실행 환경 전반의 설정
- **Unity Catalog 메타스토어 설정**: 데이터 거버넌스 관련 전역 설정

**핵심 차이**: Cloudera에서는 "설정 저장 서비스"가 눈에 보이는 별도 서비스이지만, Databricks에서는 플랫폼이 그것을 숨기고 자동으로 제공합니다.

---

### 3. HDFS (Hadoop Distributed File System)

#### Cloudera에서 이게 뭔가요?

HDFS는 **Hadoop의 핵심 분산 파일 시스템**입니다. 쉽게 말해 **엄청나게 큰 하드디스크 역할**을 하는데, 한 대의 서버가 아니라 수백~수천 대의 서버에 파일 조각을 나눠서 저장합니다.

예를 들어, 100GB짜리 파일이 있으면 이것을 128MB 조각(블록)으로 쪼개서 여러 서버에 분산 저장합니다. 그리고 각 조각을 3벌씩 복사해 두어서, 서버 한두 대가 고장나도 데이터가 안전합니다.

Cloudera에서 HDFS는 **저장 계층(Storage Layer)** 을 담당하고, YARN이 **리소스 관리 계층**을 담당한다는 것이 핵심 구조입니다.

운영자가 직접 관리해야 할 것들이 많습니다.
- NameNode(파일 목록 관리 서버), DataNode(실제 데이터 저장 서버) 운영
- 용량 모니터링, 블록 배치, 데이터 균형(Balancing), 권한 설정 등

#### Databricks에서는 어디에 해당하나요?

**HDFS에 해당하는 저장소는 Databricks 자체가 아니라 클라우드 오브젝트 스토리지**입니다.

- AWS를 쓴다면 → **Amazon S3**
- Azure를 쓴다면 → **Azure Data Lake Storage (ADLS)**
- GCP를 쓴다면 → **Google Cloud Storage (GCS)**

그리고 Databricks는 이 클라우드 스토리지 위에 **Delta Lake**와 **Unity Catalog**를 얹어서 기능을 강화합니다.

**실무 매핑 정리**
- HDFS의 "물리 저장소" 역할 → S3 / ADLS / GCS
- HDFS 위의 트랜잭션·메타 보강 → **Delta Lake** (아래에서 자세히 설명)
- HDFS 접근 권한·거버넌스 → **Unity Catalog** (external locations / volumes / grants)

**이 대응이 Cloudera → Databricks 전환에서 가장 중요한 개념입니다.**

---

### 4. Hive Metastore (HMS)

#### Cloudera에서 이게 뭔가요?

**테이블의 설계도(메타데이터)를 저장하는 서비스**입니다.

비유하자면 도서관의 **도서 목록 카드**와 같습니다. 실제 책(데이터)은 책장(HDFS/S3)에 있지만, "어떤 책이 어느 위치에 있고, 어떤 분류인지"의 목록은 도서 카드(HMS)가 보관합니다.

HMS가 저장하는 정보 예시:
- 데이터베이스 이름, 테이블 이름, 컬럼 이름과 타입
- 데이터가 실제로 어느 HDFS 경로에 있는지
- 파티션(데이터를 날짜·지역 등으로 나눈 단위) 정보
- 데이터 직렬화 방식(SerDe) 등

Hive뿐 아니라 **Impala, Spark 등 여러 서비스가 이 HMS를 공유**해서 같은 테이블을 바라볼 수 있습니다.

#### Databricks에서는 어디에 해당하나요?

가장 직접적인 대응은 **Unity Catalog의 메타스토어(metastore)** 입니다.

단, 중요한 차이가 있습니다.

| Hive Metastore | Unity Catalog |
|:---|:---|
| 테이블 메타데이터 저장 | 메타데이터 + 권한 + 계보(lineage) + 외부 스토리지 거버넌스까지 통합 |
| 테이블·파티션·위치 정보 | 테이블 외에도 파일, AI 모델, 함수까지 관리 |
| 별도 보안 서비스(Ranger) 필요 | 권한 관리가 내장됨 |

**한 줄 요약**: Hive Metastore ≈ Unity Catalog의 메타스토어 기능 (단, Unity Catalog가 훨씬 더 넓은 상위 개념)

---

### 5. Hive on Tez

#### Cloudera에서 이게 뭔가요?

사용자가 SQL을 입력하면 그것을 받아서 실제로 실행해 주는 **SQL 쿼리 엔진**입니다.

구조를 풀어보면:
- **HiveServer2**: SQL을 받는 서버 (JDBC/ODBC/Beeline/Hue 같은 도구로 연결)
- **Hive**: SQL을 파싱하고 실행 계획을 만드는 부분
- **Tez**: Hive가 만든 실행 계획을 실제로 분산 실행하는 엔진

주로 **배치성 SQL, ETL, 대용량 데이터 변환 작업**에 많이 사용됩니다. Impala보다 대화형 응답은 다소 느릴 수 있지만, 복잡한 SQL이나 ETL에서는 강점을 발휘합니다.

#### Databricks에서는 어디에 해당하나요?

용도에 따라 둘로 나뉩니다.

1. **ETL/배치 SQL 엔진 관점** → **Databricks Compute (Spark)** 위에서 돌아가는 SQL/DataFrame 작업
2. **사용자 SQL 엔드포인트 관점** → **Databricks SQL Warehouse**

**한 줄 요약**: Hive on Tez ≈ Databricks SQL Warehouse + Spark Compute
(ETL이라면 Compute가, BI성 즉시 조회라면 SQL Warehouse가 더 가깝습니다)

---

### 6. Hue

#### Cloudera에서 이게 뭔가요?

**웹 브라우저에서 SQL을 작성하고 실행하는 UI 도구**입니다.

운영자가 아닌 데이터 분석가나 엔지니어들이 복잡한 터미널 명령 없이 쉽게 클러스터를 활용할 수 있는 **포털 역할**을 합니다.

주요 기능:
- 브라우저에서 SQL 편집, 실행, 결과 확인
- Hive/Impala/HDFS 탐색
- 워크플로 생성, 쿼리 저장
- 간단한 데이터 탐색

주의할 점: Hue 안에서 보이는 권한은 실제로 Ranger 같은 보안 서비스의 권한과 분리되어 있습니다. 즉, Hue가 "게이트웨이"일 뿐이고, 실제 데이터 접근 권한은 뒤에서 Ranger가 제어합니다.

#### Databricks에서는 어디에 해당하나요?

Databricks에는 하나의 서비스로 딱 대응되지 않고, **여러 UI 기능으로 분화**되어 있습니다.

| Hue 기능 | Databricks 대응 |
|:---|:---|
| SQL 작성·실행 | **SQL Editor** |
| 데이터/테이블 탐색 | **Catalog Explorer** |
| 엔지니어링 작업 | **Notebook UI** |
| 간단한 시각화 | **Lakeview 대시보드** |

**한 줄 요약**: Hue ≈ Databricks의 Notebook + SQL Editor + Catalog Explorer (단일 서비스 대응 없음)

---

### 7. Impala

#### Cloudera에서 이게 뭔가요?

Cloudera의 **저지연(Low-latency) 고성능 SQL 엔진**입니다. "MPP(Massively Parallel Processing)"라고 하는 방식으로 여러 서버가 동시에 쿼리를 나눠 처리해서 빠른 응답을 냅니다.

내부적으로 `impalad`라는 데몬 프로세스들이 병렬로 쿼리 조각을 실행합니다.

주요 용도:
- BI 도구(Tableau, Power BI 등)와 연결해 대시보드 조회
- 즉시 결과가 필요한 애드혹(Ad-hoc) 쿼리
- HDFS나 Kudu 기반 데이터의 고성능 분석
- JDBC/ODBC 연동에 적합

Hive보다 대화형 응답이 훨씬 빠른 것이 강점입니다.

#### Databricks에서는 어디에 해당하나요?

가장 직접적인 대응은 **Databricks SQL Warehouse**입니다.

SQL Warehouse는 Databricks SQL에서 데이터를 SQL로 조회할 수 있는 컴퓨트 리소스이며, Databricks는 공식적으로 대부분의 경우 **Serverless SQL Warehouse** 사용을 권장합니다.

Cloudera에서 Impala가 "빠른 SQL 엔진"이었다면, Databricks에서는 **SQL Warehouse가 그 자리**에 옵니다.

차이점:
- Impala는 Hadoop 생태계 안의 별도 MPP 엔진
- SQL Warehouse는 Databricks 플랫폼 안의 SQL 전용 컴퓨트
- Databricks에서는 메타스토어/권한/실행/UI가 Impala보다 더 통합적으로 묶여 있음

**한 줄 요약**: Impala ≈ Databricks SQL Warehouse (이건 비교적 1:1에 가장 가깝습니다)

---

### 8. Kudu

#### Cloudera에서 이게 뭔가요?

Hadoop 플랫폼용 **컬럼형(Columnar) 저장 엔진**입니다.

일반적인 파일 저장(HDFS)과 달리, **분석에 특화된 저장 방식**을 사용합니다. 특히 데이터를 수정(UPSERT, Update+Insert)하거나 실시간에 가깝게 빠른 읽기가 필요한 경우에 강합니다.

주요 특징:
- 컬럼 단위로 데이터를 저장해 분석 쿼리에 최적화
- 일부 업데이트/UPSERT 패턴에 유리
- Impala와 조합해 저지연 분석에 자주 사용됨
- "파일 시스템"보다는 "분산 저장 엔진" 성격이 강함

#### Databricks에서는 어디에 해당하나요?

가장 가까운 대응은 **Delta Lake 테이블**입니다.

Delta Lake는 Parquet 파일(컬럼형 저장 형식) 위에 **트랜잭션 로그(Transaction Log)** 를 더해서 다음을 제공합니다.
- ACID 트랜잭션 (데이터가 중간에 깨지지 않도록 보장)
- Merge/Update/Delete 지원
- 스트리밍과 배치를 함께 처리하는 통합 모델
- 확장 가능한 메타데이터 처리

Kudu가 "분석 친화적 저장 엔진 + 업데이트 친화성"을 목표로 했다면, Databricks에서는 **Delta Lake**가 그 역할을 담당합니다.

완전히 같지는 않습니다.
- Kudu: 별도 분산 스토리지 엔진
- Delta Lake: 클라우드 오브젝트 스토리지 위에 놓이는 테이블 포맷/저장 계층

하지만 실무에서 **"분석용 운영 테이블 저장 계층"** 으로 비교하면 가장 가깝습니다.

**한 줄 요약**: Kudu ≈ Delta Lake (특히 UPSERT/Merge 가능한 분석용 테이블 계층으로 이해하세요)

---

### 9. Oozie

#### Cloudera에서 이게 뭔가요?

**여러 작업을 순서대로 조율하고 스케줄링하는 워크플로 관리 서비스**입니다.

쉽게 비유하면 **공정 자동화 지휘자**와 같습니다. "먼저 A 작업을 하고, 완료되면 B와 C를 동시에 실행하고, 둘 다 끝나면 D를 실행해라" 같은 흐름을 정의하고 실행합니다.

주요 기능:
- 시간 기반 스케줄링 (매일 오전 2시에 실행 등)
- 파일 도착/데이터 준비 상태 기반 트리거 (특정 파일이 도착하면 시작)
- Hive, Spark, MapReduce 등 여러 작업의 DAG(흐름도) 관리
- 실패 시 재시도, 선후행 의존성 제어

DAG란? — Directed Acyclic Graph의 약자로, "작업들의 순서 흐름도"입니다. 화살표로 연결된 작업 그래프에서 사이클(무한 반복)이 없는 구조입니다.

#### Databricks에서는 어디에 해당하나요?

이건 거의 명확하게 **Lakeflow Jobs** 입니다.

Lakeflow Jobs는 Databricks의 워크플로 자동화 서비스로, 다음을 지원합니다.
- 여러 태스크(작업)를 조정·실행
- 반복 실행되는 작업과 복잡한 워크플로 관리
- External location에 새 파일이 도착하면 Job을 트리거하는 기능

이는 Oozie의 전형적인 사용 패턴과 매우 유사합니다.

**한 줄 요약**: Oozie ≈ Lakeflow Jobs (이건 가장 이해하기 쉬운 1:1 대응입니다)

---

### 10. Ranger

#### Cloudera에서 이게 뭔가요?

**플랫폼 전반의 데이터 보안을 관리하는 프레임워크**입니다.

쉽게 비유하면 **회사 건물의 출입 통제 시스템**입니다. 어떤 직원(사용자)이 어떤 방(데이터)에 들어갈 수 있는지 정책을 정의하고, 모든 출입 기록을 남깁니다.

주요 기능:
- 사용자/그룹별 접근 권한 정책 정의
- HDFS, Hive, HBase 등 여러 서비스에 걸친 접근 제어
- 감사(Audit) 로그 생성 — "언제 누가 어떤 데이터에 접근했는지" 기록
- 보안 관리자 중심의 중앙 정책 관리
- Resource-based 정책 (특정 테이블/경로 단위) + Tag-based 정책 (메타데이터 태그 기반) 지원
- Ranger RMS: Hive 정책과 HDFS ACL(파일 접근 제어) 동기화 기능

#### Databricks에서는 어디에 해당하나요?

가장 직접적인 대응은 **Unity Catalog**입니다.

Unity Catalog는 Databricks에 내장된 통합 데이터/AI 거버넌스 솔루션입니다.
- catalog, schema, table, volume, AI 모델, 함수 등 다양한 객체에 대해 중앙 권한 관리
- 데이터 계보(lineage) 자동 추적
- 클라우드 간 데이터 공유(Delta Sharing) 지원

차이점:
- Ranger: Hadoop 생태계의 여러 독립 서비스를 가로질러 붙는 보안 프레임워크
- Unity Catalog: Databricks 플랫폼 내부의 기본 거버넌스 계층 (더 Databricks-native하고, 데이터/AI 자산 전반을 한 번에 관리)

**한 줄 요약**: Ranger ≈ Unity Catalog (이것도 꽤 직접적인 대응입니다)

---

### 11. Tez

#### Cloudera에서 이게 뭔가요?

**Hive 쿼리를 실제로 분산 실행하는 내부 실행 엔진**입니다.

사용자가 Hive에 SQL을 입력하면, Hive가 그것을 파싱하고 실행 계획을 만듭니다. 그런데 이 실행 계획을 실제로 여러 서버에 나눠 돌리는 것이 바로 Tez입니다.

구조를 간단히 보면:
- 사용자 → SQL 입력 → HiveServer2 수신 → Hive가 실행 계획(DAG) 생성 → **Tez가 실제 분산 실행**

Tez는 예전의 MapReduce보다 더 유연하고 효율적인 실행 모델을 제공합니다. 사용자가 직접 "Tez SQL"을 쓰는 것이 아니라, Hive가 자동으로 Tez를 활용하는 방식입니다.

#### Databricks에서는 어디에 해당하나요?

Databricks에는 Tez에 대응하는 **별도 제품이 없습니다.** 이 역할은 **Spark 실행 엔진 내부로 흡수**되어 있습니다.

- Hive on Tez에서 Tez가 맡던 분산 DAG 실행 역할
- → Databricks에서는 **Spark engine이 내부적으로 수행**

사용자 관점에서는 notebook, job, SQL warehouse를 사용하는 것이지, "Tez에 해당하는 독립 서비스"를 직접 관리하지 않습니다.

**한 줄 요약**: Tez ≈ Databricks 내부 Spark 실행 레이어 (독립 서비스 대응 없음)

---

### 12. YARN (MR2 Included)

#### Cloudera에서 이게 뭔가요?

Hadoop의 **리소스 관리 및 스케줄링 계층**입니다. 앞서 HDFS가 "저장 계층"이라면, YARN은 **"CPU·메모리 자원을 어떻게 배분할지 결정하는 계층"** 입니다.

Spark, Tez, MapReduce 같은 실행 엔진들이 작업을 돌릴 때 "CPU 몇 개, 메모리 몇 GB 줘"라고 YARN에게 요청합니다. YARN은 클러스터 전체의 가용 자원을 파악하고 요청들을 스케줄링해 처리합니다.

주요 기능:
- 클러스터 전체 자원 스케줄링
- 애플리케이션별 컨테이너(CPU+메모리 단위) 할당
- 여러 팀이 자원을 나눠 쓰는 멀티테넌시(Multi-tenancy) 지원

#### Databricks에서는 어디에 해당하나요?

Databricks에는 YARN이 **사용자에게 드러나지 않습니다.** 이 역할은 Databricks의 컨트롤 플레인과 클라우드 VM 오케스트레이션 내부로 흡수되어 있습니다.

Databricks에서는 YARN처럼 큐(Queue)와 컨테이너를 직접 조작하기보다, **cluster/compute 또는 serverless 자원 단위로 관리**합니다.

핵심 차이:
- Cloudera: 사용자가 YARN 자원 모델을 자주 의식하고 직접 관리
- Databricks: 사용자는 cluster/warehouse를 보고, 내부 스케줄링은 플랫폼이 알아서 처리

**한 줄 요약**: YARN ≈ Databricks 내부 Compute/Resource 관리 플레인 (직접 대응되는 사용자 노출 서비스 없음)

---

### 13. YARN Queue Manager

#### Cloudera에서 이게 뭔가요?

YARN의 **Capacity Scheduler(용량 스케줄러)를 관리하는 UI 도구**입니다.

쉽게 말해, **팀별로 자원 배분 규칙을 만드는 관리자 도구**입니다.

예를 들어:
- "데이터팀은 최대 40%의 클러스터 자원만 쓸 수 있다"
- "AI팀은 최소 20%를 항상 보장받는다"
- "야간 배치 작업은 우선순위를 높게 준다"

이런 정책을 큐(Queue) 단위로 계층적으로 설정할 수 있습니다. 부서별·팀별·워크로드별로 자원 거버넌스를 하는 핵심 운영 도구입니다.

#### Databricks에서는 어디에 해당하나요?

YARN처럼 "큐 트리"를 직접 만드는 방식은 없지만, 비슷한 목적을 위한 기능들이 있습니다.

- **Compute 정책**: 어떤 팀이 어떤 compute를 어떤 크기로 쓸지 제어
- **SQL Warehouse sizing/scaling/queuing**: SQL 실행 자원의 크기, 자동 확장, 대기열 동작 설정
- **Job cluster vs All-purpose compute 분리**: 작업 특성에 따라 분리 운영
- **Serverless와 classic compute 선택 전략**: 용도에 맞는 자원 유형 선택

**한 줄 요약**: YARN Queue Manager ≈ Databricks Compute 정책 + SQL Warehouse 거버넌스 설정 (1:1 대응은 아님)

---

### 14. ZooKeeper

#### Cloudera에서 이게 뭔가요?

**분산 서비스들이 서로 상태를 맞추고 조율하는 "보조 인프라"** 입니다.

사용자가 직접 "ZooKeeper 써!"라고 하지 않지만, Hadoop 생태계의 많은 서비스들이 뒤에서 ZooKeeper를 활용합니다.

ZooKeeper가 하는 일:
- **리더 선출**: 여러 서버 중 누가 "주인 역할"을 할지 결정
- **서비스 디스커버리**: "저 서비스는 어느 서버에 있나?" 찾기
- **설정/상태 동기화**: 여러 서버가 같은 설정을 바라보도록 유지
- **분산 락**: 동시에 같은 자원에 접근하지 않도록 제어

HBase, Kafka, YARN/Hadoop 구성요소 등의 보조 인프라로 동작합니다.

#### Databricks에서는 어디에 해당하나요?

**직접 대응하는 서비스가 없습니다.** 이런 종류의 분산 조율 기능은 Databricks 관리 서비스와 클라우드 네이티브 제어 계층 내부로 완전히 흡수되어 있습니다.

사용자는 Databricks에서 ZooKeeper를 직접 운영할 필요가 없습니다.

**한 줄 요약**: ZooKeeper ≈ Databricks 내부 관리형 coordination 레이어 (사용자에게 보이는 대응 서비스 없음)

---

## 카테고리별 종합 비교

이번에는 개별 서비스가 아니라 **"무슨 일을 하는가"** 기준으로 묶어 비교합니다.

---

### 카테고리 1. 데이터 엔지니어링 (ETL & Pipeline)
> **ETL이란?** 데이터를 추출(Extract)하고, 변환(Transform)하고, 저장(Load)하는 작업입니다.

#### Cloudera: CDE (Cloudera Data Engineering)

Apache Spark를 기반으로 하는 서버리스 데이터 엔지니어링 서비스입니다.
- Kubernetes를 활용해 리소스를 자동 할당합니다.
- Apache Airflow와 통합되어 복잡한 작업 스케줄링을 지원합니다.

#### Databricks: Workflows (Jobs) + Delta Live Tables

- **Databricks Workflows (Jobs)**: Spark 작업을 스케줄링하고 DAG 형태로 파이프라인을 관리합니다.
- **Delta Live Tables (DLT)**: SQL이나 Python으로 선언형(Declarative) ETL을 작성하면, 파이프라인 실행과 데이터 품질 관리를 자동화해 줍니다.

> **선언형 ETL이란?** "어떻게 처리할지(How)"가 아니라 "무엇을 원하는지(What)"만 정의하면 시스템이 알아서 실행하는 방식입니다.

**주요 차이**: Databricks가 선언형 파이프라인(DLT)에서 더 강점을 보입니다.

---

### 카테고리 2. 데이터 웨어하우징 (SQL Analytics)
> **데이터 웨어하우스란?** 정형화된 대용량 데이터를 저장하고 SQL로 분석하는 시스템입니다.

#### Cloudera: CDW (Cloudera Data Warehouse)

Apache Hive(LLAP)와 Impala 엔진을 사용합니다.
- 클라우드에서 "Virtual Warehouse"를 생성해 독립적인 쿼리 성능을 보장합니다.
- 대규모 동시 접속 처리에 최적화되어 있습니다.

#### Databricks: Databricks SQL (DB SQL)

최근 Databricks가 가장 주력하는 서비스입니다.
- **Photon 엔진**: C++ 기반의 고성능 SQL 실행 엔진으로 매우 빠릅니다.
- **Serverless SQL Warehouse**: 서버 관리 없이 SQL 쿼리 실행 가능합니다.
- Tableau, Power BI 같은 BI 도구와의 연결성이 매우 뛰어납니다.

**주요 차이**: CDW는 전통적 SQL 강세, Databricks SQL은 속도·서버리스·BI 연결성 강조

---

### 카테고리 3. 머신러닝 & AI

#### Cloudera: CML (Cloudera Machine Learning)

Cloudera Data Science Workbench(CDSW)의 진화형입니다.
- Jupyter, RStudio 등 익숙한 IDE를 컨테이너 환경에서 제공합니다.
- 모델 배포 및 모니터링 기능을 포함합니다.
- 최근에는 LLM(대형 언어 모델)을 위한 AI Studio 기능이 강화되었습니다.

#### Databricks: Mosaic AI (이전 Databricks ML)

MLflow라는 업계 표준 오픈소스를 만든 곳답게, **실험 추적 및 모델 관리가 매우 강력**합니다.
- 통합 노트북 환경에서 데이터 준비부터 배포까지 원스톱으로 이루어집니다.
- MosaicML 인수를 통해 생성형 AI(GenAI) 모델 학습 분야에서 강점을 보입니다.

**주요 차이**: Databricks가 GenAI 및 MLOps 생태계에서 우위를 보입니다.

---

### 카테고리 4. 데이터 스트리밍 (Real-time)
> **스트리밍이란?** 실시간으로 쏟아지는 데이터(예: 센서, 로그, 거래 기록)를 즉시 처리하는 것입니다.

#### Cloudera: CDF (Cloudera DataFlow)

Apache NiFi, Kafka, Flink를 하나로 묶은 서비스입니다.
- **Apache NiFi**: GUI(그래픽 인터페이스) 기반의 No-code 데이터 수집 도구. 코드 없이 마우스로 데이터 흐름을 설계할 수 있습니다.
- 엣지 컴퓨팅(Edge2AI) 시나리오에 강합니다. (공장 기기, IoT 센서 등 현장 데이터 수집)

#### Databricks: Delta Live Tables + Spark Structured Streaming

Databricks는 스트리밍을 별도 도구보다는 **Spark의 연장선**으로 처리합니다.
- 실시간 데이터를 테이블 형태로 자동 처리하는 **Delta Live Tables**가 CDF의 스트리밍 분석 기능을 담당합니다.
- **단점**: NiFi 같은 GUI 기반의 범용 수집 도구 역할은 상대적으로 약합니다.

**주요 차이**: Cloudera는 수집과 복잡한 스트리밍 로직(No-code 포함)에 강점, Databricks는 Spark 기반 분석 스트리밍에 강점

---

### 카테고리 5. 거버넌스 & 보안 (Security & Governance)
> **거버넌스란?** 데이터에 "누가 접근할 수 있는지", "어디서 왔는지", "어디로 갔는지"를 관리하는 체계입니다.

#### Cloudera: SDX (Shared Data Experience)

Apache Ranger와 Apache Atlas를 기반으로 합니다.
- **핵심 원칙**: "한 번 설정하면 어디서든 적용된다" — 하이브리드 클라우드(온프레미스 + 클라우드) 전체의 보안 정책과 데이터 카탈로그를 통합 관리합니다.

#### Databricks: Unity Catalog

Databricks의 모든 자산(파일, 테이블, AI 모델, 대시보드)에 대한 **통합 거버넌스 레이어**입니다.
- 클라우드 간 데이터 공유 기능인 **Delta Sharing**이 매우 강력합니다.
- 최근에는 AI 모델 거버넌스까지 확장되었습니다.

**주요 차이**: SDX는 하이브리드 환경(온프레미스+클라우드)에 강점, Unity Catalog는 클라우드 네이티브 환경에 최적화

---

## 아키텍처 사고방식의 차이

Cloudera에서 Databricks로 넘어갈 때 핵심은 **"서비스 이름 치환"이 아니라 아키텍처 사고방식의 전환**입니다.

### Cloudera의 사고방식

```
저장소    → HDFS
메타데이터 → Hive Metastore (HMS)
보안/권한  → Ranger
SQL 실행   → Hive / Impala
실행 엔진  → Tez / Spark
스케줄링   → Oozie
자원 관리  → YARN
운영 보조  → ZooKeeper / Solr
```

각 기능이 별도 서비스로 눈에 보이고, 운영자가 하나하나 직접 관리합니다.

### Databricks의 사고방식

```
저장소           → 클라우드 오브젝트 스토리지 (S3/ADLS/GCS)
테이블 계층       → Delta Lake
메타/권한/계보    → Unity Catalog
SQL 실행         → SQL Warehouse
엔지니어링 실행   → Compute (Spark)
스케줄링         → Lakeflow Jobs
자원 관리        → 플랫폼이 내부에서 자동 처리
코디네이션       → 플랫폼이 내부에서 자동 처리
```

내부 인프라 관리를 플랫폼이 숨기고, 사용자는 더 높은 추상화 수준의 기능에 집중합니다.

---

## 어떤 플랫폼이 우리 조직에 맞을까요?

### Cloudera가 유리한 경우

- 기존에 Hadoop 환경을 사용하고 있어서 점진적으로 이전해야 하는 경우
- 보안·규제가 엄격하고 **온프레미스(사내 서버)와 클라우드를 병행**해야 하는 대기업
- 특정 국가/산업 규정으로 인해 데이터가 자체 데이터센터에 있어야 하는 경우

### Databricks가 유리한 경우

- **클라우드 환경**에서 AI와 머신러닝을 핵심 가치로 두는 조직
- 데이터 엔지니어링과 분석을 하나의 통합 플랫폼(Lakehouse)으로 단순화하려는 경우
- 인프라 관리 부담을 줄이고 데이터/AI 작업에 집중하고 싶은 경우
- 최신 GenAI(생성형 AI) 모델 개발 및 운영이 필요한 경우

---

## 전체 매핑 최종 요약

| Cloudera 서비스 | Databricks 대응 | 대응 정밀도 |
|:---|:---|:---|
| HDFS | S3/ADLS/GCS + Delta Lake + Unity Catalog external locations | 구조 전환 필요 |
| Hive Metastore | Unity Catalog metastore | 비교적 직접 대응 |
| Hive on Tez | SQL Warehouse + Spark Compute | 용도에 따라 분리 |
| Impala | SQL Warehouse | 1:1에 가장 가까움 |
| Kudu | Delta Lake | 비교적 직접 대응 |
| Oozie | Lakeflow Jobs | 1:1에 가장 가까움 |
| Ranger | Unity Catalog | 비교적 직접 대응 |
| Hue | Notebook + SQL Editor + Catalog Explorer | UI 기능으로 분화 |
| Tez | Spark 내부 실행 레이어 | 독립 서비스 없음 |
| YARN | Databricks 내부 Compute 관리 | 플랫폼이 흡수 |
| YARN Queue Manager | Compute 정책 + SQL Warehouse 거버넌스 | 유사 기능으로 분화 |
| ZooKeeper | Databricks 내부 coordination 레이어 | 플랫폼이 흡수 |
| Core Configuration | Workspace/Compute 설정 (컨트롤 플레인) | 플랫폼이 흡수 |
| CDP-INFRA-SOLR | Unity Catalog 감사 기능 + 외부 로그 분석 시스템 | 직접 대응 없음 |
| CDE | Workflows (Jobs) + Delta Live Tables | 비교적 직접 대응 |
| CDW | Databricks SQL | 비교적 직접 대응 |
| CML | Mosaic AI (MLflow 기반) | 비교적 직접 대응 |
| CDF | Delta Live Tables + Spark Structured Streaming | 일부 기능 차이 있음 |
| SDX | Unity Catalog | 비교적 직접 대응 |

---

*이 문서는 GPT와 Gemini의 답변을 바탕으로 초보자도 이해할 수 있도록 통합·재작성되었습니다.*
