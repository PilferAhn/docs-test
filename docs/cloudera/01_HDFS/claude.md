# HDFS (Claude 정리)

> GPT 답변 + Gemini 답변을 종합 정리한 버전

---

## 1. HDFS란?

**HDFS(Hadoop Distributed File System)** 는 Hadoop의 핵심 분산 파일 시스템입니다.

한 마디로 요약하면:
> **"거대한 파일을 작게 쪼개어 여러 대의 서버에 복사본과 함께 흩뿌려 놓고, 사서(NameNode)가 그 위치를 장부에 적어 관리하는 시스템"**

쉽게 비유하면 **수백~수천 대의 서버에 걸쳐 있는 거대한 공유 하드디스크**입니다.
100GB짜리 파일을 128MB 조각(블록)으로 쪼개서 여러 서버에 분산 저장하고,
각 조각을 3벌씩 복사해 두어 서버 한두 대가 고장 나도 데이터가 안전합니다.

---

## 2. 핵심 전략: "나눠서, 복사해서, 흩어놓는다"

| 전략 | 설명 |
|:---|:---|
| **블록(Block) 분할** | 큰 파일을 128MB(또는 256MB) 조각으로 쪼갭니다 |
| **분산 저장** | 쪼개진 조각들을 여러 서버(DataNode)에 나누어 저장합니다 |
| **복제(Replication)** | 각 조각을 기본 3군데의 서로 다른 서버에 복사해 둡니다 |

---

## 3. 파일 및 폴더 구조

### 사용자 관점 (논리적 구조)

사용자 눈에는 일반 PC 폴더와 동일한 트리 구조로 보입니다.

```
/data/raw/2025/04/20/sales.csv
/user/hive/warehouse/orders/
/tmp/job123/output/
```

명령어도 Linux와 유사합니다.

```bash
hdfs dfs -ls /data/raw
hdfs dfs -put sales.csv /data/raw/
```

### 시스템 관점 (물리적 구조)

실제 DataNode 디스크에는 폴더 구조 그대로 저장되지 않습니다.
대신 블록 파일로 쪼개져 내부 관리 경로에 저장됩니다.

```
/disk1/hdfs/data/current/BP-xxxx/current/finalized/subdir0/subdir1/blk_1073741825
```

즉, **논리 경로와 물리 저장 경로는 완전히 분리**됩니다.

---

## 4. 핵심 구성 요소 (Master-Slave 구조)

### ① NameNode - "도서관 사서"

- **역할:** 파일 시스템의 **메타데이터(설계도)** 를 관리합니다.
- **저장 정보:** 파일명, 디렉터리 구조, 각 파일의 블록 목록, 블록이 저장된 DataNode 위치, 소유자/권한 등
- **특징:** 메모리(RAM)에서 관리하므로 빠르지만, NameNode가 죽으면 전체 데이터 접근이 불가합니다.
- **저장하지 않는 것:** 실제 파일 내용 (그건 DataNode의 역할)

### ② DataNode - "책꽂이 창고"

- **역할:** **실제 데이터(블록)** 를 디스크에 저장합니다.
- **특징:** 클라이언트는 NameNode에게 위치를 물어본 뒤, 실제 데이터는 DataNode와 직접 주고받습니다.
- **보고:** DataNode는 NameNode에게 heartbeat(생존 신호)와 block report(보유 블록 목록)를 주기적으로 전송합니다.

### ③ 역할 분리의 핵심

```
NameNode = "어디에 있는가" (메타데이터)
DataNode = "실제 데이터"  (블록 파일)
```

---

## 5. 파일 Write 흐름 (쓰기 시나리오)

사용자가 `movie.mp4` 파일을 HDFS에 저장할 때:

1. **요청:** 클라이언트 → NameNode: "이 파일 저장하고 싶어"
2. **계획:** NameNode → 클라이언트: "블록 A, B, C로 쪼개서 DN1, DN5, DN9에 저장해"
3. **전송:** 클라이언트 → 첫 번째 DataNode로 데이터 전송
4. **파이프라인 복제:** DN1 → DN4 → DN7 순서로 블록 복사 (복제본 생성)
5. **완료 보고:** 모든 복제 완료 후 NameNode에 확정 보고

```
클라이언트 ──► DN1 ──복제──► DN4 ──복제──► DN7
                 └── ACK 역방향 전달 ──────────┘
```

---

## 6. 파일 Read 흐름 (읽기 시나리오)

1. **요청:** 클라이언트 → NameNode: "이 파일 어디 있어?"
2. **응답:** NameNode → 클라이언트: "블록 위치 목록" 반환
3. **직접 읽기:** 클라이언트가 가장 가까운 DataNode에서 직접 읽음
   - 이를 **Data Locality** 라고 합니다 (데이터 근처에서 계산)

**핵심:** 실제 데이터 전송은 NameNode를 거치지 않으므로 NameNode 병목 없음

---

## 7. 복제 배치 전략 (Rack Awareness)

단순히 아무 서버 3대가 아니라, 장애 도메인을 고려해 배치합니다.

| 복제본 | 배치 위치 |
|:---|:---|
| 복제본 1 | 같은 랙 내 노드 |
| 복제본 2 | 같은 랙 내 다른 노드 |
| 복제본 3 | **다른 랙**의 노드 |

→ 랙 단위 장애가 발생해도 다른 랙에 복제본이 보존됩니다.

---

## 8. 장점과 한계

### 장점

| 장점 | 설명 |
|:---|:---|
| 장애 복구 (Fault Tolerance) | 서버 한두 대가 고장 나도 복제본으로 자동 복구 |
| 저사양 하드웨어 활용 | 고가 장비 없이 일반 서버(Commodity Hardware) 여러 대로 대용량 구성 가능 |
| 무한 확장 (Scale-out) | 서버를 추가하면 용량이 선형으로 증가 |
| 대용량 배치 처리 최적화 | 순차적으로 크게 읽는 배치 분석에 강함 |

### 단점 및 주의사항

| 단점 | 설명 |
|:---|:---|
| 수정 어려움 (Append Only) | 한 번 저장된 파일의 중간 수정(Update)이 어려움. Write Once, Read Many 철학 |
| 작은 파일 문제 (Small File Problem) | 작은 파일 수백만 개 → NameNode 메모리 과부하 |
| 낮은 지연 응답 부적합 | 실시간 DB처럼 즉각 응답이 필요한 용도에 부적합 |
| NameNode 단일 장애점 | NameNode 다운 시 전체 접근 불가 → HA 구성 필수 |

---

## 9. Cloudera에서의 역할

HDFS는 Hadoop 아키텍처의 **저장 계층(Storage Layer)** 입니다.

```
실행 엔진 (Hive, Impala, Spark, MapReduce)
           ↓ 데이터 읽기/쓰기
        HDFS (저장 계층)
           ↓ 리소스 요청
        YARN (리소스 관리 계층)
```

운영자가 직접 관리해야 할 것들:
- **NameNode HA** 구성 및 모니터링
- **DataNode** 용량 모니터링, 블록 균형(Balancing)
- **접근 권한** 설정 (Ranger 연계)
- **fsck** 로 블록 무결성 정기 점검

---

## 10. Databricks 대응

**HDFS의 역할은 Databricks 제품이 아니라 클라우드 오브젝트 스토리지가 대체**합니다.

| 클라우드 | HDFS 대체 저장소 |
|:---|:---|
| AWS | Amazon S3 |
| Azure | Azure Data Lake Storage (ADLS) |
| GCP | Google Cloud Storage (GCS) |

Databricks는 이 클라우드 스토리지 위에 추가 기능을 얹습니다.

| HDFS 기능 | Databricks 대응 |
|:---|:---|
| 물리 파일 저장 | S3 / ADLS / GCS |
| 트랜잭션·버전 관리 | **Delta Lake** |
| 접근 권한·거버넌스 | **Unity Catalog** (external locations / volumes / grants) |
| 파일 포맷 | Parquet → **Delta 포맷** |

### 왜 이 전환이 핵심인가

Cloudera → Databricks 전환에서 HDFS 대체가 연쇄 작업의 시작점입니다.

- HDFS 위에 올라가 있던 **Hive, Impala, Spark** 등이 모두 클라우드 스토리지로 이전해야 함
- 데이터 마이그레이션, 권한 재설정, 파일 포맷 변환(→ Delta Lake)이 수반됨
- 운영자가 직접 관리하던 NameNode/DataNode 관리 부담이 클라우드로 위임됨

---

## 한 줄 요약

**HDFS = Cloud Object Storage(S3/ADLS/GCS) + Delta Lake + Unity Catalog**
