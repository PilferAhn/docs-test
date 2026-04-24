# Impala 아키텍처 완전 정복
### — 처음 보는 사람도 이해할 수 있도록 —

---

## Impala가 빠른 이유 한 줄 요약

> **여러 서버가 동시에 일을 나눠서 처리하고, 항상 메모리에 떠 있어서 즉시 응답한다.**

---

## 전체 구성 요소

Impala는 세 가지 컴포넌트로 구성됩니다.

```
┌─────────────────────────────────────────────────────────┐
│                   Impala 클러스터                        │
│                                                         │
│  adm1 ┌─────────────────┐  ┌─────────────────────────┐ │
│       │  Catalog Server  │  │      StateStore         │ │
│       │  (메타데이터 관리)│  │  (데몬 상태 모니터링)   │ │
│       └────────┬─────────┘  └──────────┬──────────────┘ │
│                │                        │               │
│                └──────────┬─────────────┘               │
│                           │ 메타 정보 + 상태 전파         │
│              ┌────────────┼────────────┐                │
│              ▼            ▼            ▼                │
│  hdw1  ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  hdw2  │  Impala  │ │  Impala  │ │  Impala  │          │
│  hdw3  │  Daemon  │ │  Daemon  │ │  Daemon  │          │
│        │(impalad) │ │(impalad) │ │(impalad) │          │
│        └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────┘
```

---

## 컴포넌트별 역할

### 1. Impala Daemon (impalad) — 실제 일꾼

**어디에**: 데이터 노드(hdw1, hdw2, hdw3)에 각각 설치

**하는 일**:
- 쿼리를 직접 실행하는 엔진
- HDFS/Kudu에서 데이터를 읽어 처리
- 클라이언트 접속도 여기에 함 (포트 21050)

```
hdw1의 impalad  →  hdw1에 있는 데이터 담당
hdw2의 impalad  →  hdw2에 있는 데이터 담당
hdw3의 impalad  →  hdw3에 있는 데이터 담당
```

HDFS는 파일을 여러 노드에 나눠 저장하기 때문에, 각 노드의 impalad가 자기 노드 데이터를 직접 읽습니다. 네트워크를 거치지 않아서 빠릅니다. 이것을 **데이터 지역성(Data Locality)** 이라고 합니다.

---

### 2. Catalog Server — 도서관 사서

**어디에**: 관리 노드(adm1)에 설치, 클러스터 전체에 1개

**하는 일**:
- Hive Metastore에서 테이블 정보를 읽어 모든 Daemon에 전파
- 테이블이 새로 생기거나 변경되면 즉시 알림

```
Hive Metastore  →  Catalog Server  →  모든 impalad에 전파
(DB에 저장된       (변경 감지 및       (각 데몬이 최신
 메타데이터)        변경 알림)          정보를 가짐)
```

**없으면 어떻게 되나**: 테이블을 새로 만들어도 Impala가 인식 못 합니다. 그래서 `INVALIDATE METADATA` 명령이 필요했던 것도 이 동기화 때문입니다.

---

### 3. StateStore — 건강 체크 담당

**어디에**: 관리 노드(adm1)에 설치, 클러스터 전체에 1개

**하는 일**:
- 모든 Daemon이 살아있는지 주기적으로 확인 (heartbeat)
- 죽은 Daemon을 감지해서 다른 Daemon들에게 알림
- Daemon들이 서로의 상태를 알 수 있게 중계

```
StateStore가 hdw2의 Daemon 장애 감지
    ↓
hdw1, hdw3 Daemon에게 "hdw2 못 씀" 알림
    ↓
이후 쿼리는 hdw1, hdw3만 사용
```

**없으면 어떻게 되나**: Daemon들이 서로의 상태를 모르게 됩니다. StateStore가 죽어도 기존 쿼리는 계속 실행되지만, 장애 감지가 안 됩니다.

---

## 쿼리가 실행되는 흐름

```
impala-shell -i hdw1.ktwings.dd.io:21050
```

위 명령으로 접속하면 hdw1의 impalad가 **Coordinator(조율자)** 가 됩니다.

```
1. 클라이언트가 hdw1에 접속해서 쿼리 전송
        SELECT SUM(total_volume) FROM traffic_demo.traffic_volume;

2. hdw1 (Coordinator)가 쿼리 계획 수립
        "이 테이블 데이터가 hdw1, hdw2, hdw3에 나뉘어 있구나"

3. 각 노드에 작업 분배
        hdw1 → 자기 데이터 처리
        hdw2 → 자기 데이터 처리
        hdw3 → 자기 데이터 처리

4. 병렬 처리 (동시에 실행)
        hdw1: SUM = 1,200,000
        hdw2: SUM = 980,000
        hdw3: SUM = 1,050,000

5. hdw1 (Coordinator)가 결과 취합
        최종 SUM = 1,200,000 + 980,000 + 1,050,000 = 3,230,000

6. 클라이언트에 반환
```

---

## Coordinator란?

접속한 노드가 그 쿼리의 **Coordinator** 가 됩니다.

```bash
# hdw1에 접속 → hdw1이 Coordinator
impala-shell -i hdw1.ktwings.dd.io:21050

# hdw2에 접속 → hdw2가 Coordinator
impala-shell -i hdw2.ktwings.dd.io:21050
```

Coordinator의 역할:
- 쿼리를 받아서 실행 계획 수립
- 다른 Daemon들에게 작업 분배
- 결과를 모아서 클라이언트에 반환

**어디에 접속해도 동일한 결과가 나오는 이유**: 접속 노드만 Coordinator가 바뀔 뿐, 나머지 처리는 동일하게 분산됩니다.

```bash
# 세 곳 모두 동일한 결과
impala-shell -i hdw1.ktwings.dd.io:21050 -q "SELECT COUNT(*) FROM traffic_demo.traffic_volume;"
impala-shell -i hdw2.ktwings.dd.io:21050 -q "SELECT COUNT(*) FROM traffic_demo.traffic_volume;"
impala-shell -i hdw3.ktwings.dd.io:21050 -q "SELECT COUNT(*) FROM traffic_demo.traffic_volume;"
```

---

## 이 프로젝트의 Impala 구성

```
adm1.ktwings.dd.io  →  Catalog Server + StateStore (관리 전담)
hdw1.ktwings.dd.io  →  Impala Daemon  ← 스크립트에서 접속하는 곳
hdw2.ktwings.dd.io  →  Impala Daemon
hdw3.ktwings.dd.io  →  Impala Daemon
```

스크립트에서 `hdw1`에 접속하는 이유:
- 어디에 접속해도 동일하게 동작
- hdw1을 관례적으로 첫 번째 접속 노드로 사용
- 부하 분산이 필요하다면 로드밸런서를 앞에 두기도 함

---

## 자주 쓰는 운영 명령어

```sql
-- 메타데이터 전체 새로고침 (테이블 새로 만든 뒤 인식 안 될 때)
INVALIDATE METADATA;

-- 특정 테이블만 새로고침
INVALIDATE METADATA traffic_demo.traffic_volume;

-- 통계 수집 (쿼리 최적화에 필요)
COMPUTE STATS traffic_demo.traffic_volume;

-- 현재 연결된 Coordinator 확인
SELECT version();

-- 실행 중인 쿼리 확인
SELECT * FROM sys.impala_query_log LIMIT 10;
```

---

## Hive와 비교: 왜 Impala가 빠른가

| | Impala | Hive (Tez) |
|:---|:---|:---|
| 실행 방식 | impalad가 메모리에 항상 떠 있음 | 쿼리마다 Tez 컨테이너 새로 띄움 |
| 시작 시간 | 즉시 | 10~30초 |
| 중간 데이터 | 메모리에서 처리 | 디스크에 임시 파일 씀 |
| 장애 시 | 데이터 손실 가능 (메모리) | 디스크에 남아 재시도 가능 |
| 적합한 작업 | 빠른 조회, 대시보드 | 대용량 배치, INSERT ETL |

---

## 자주 하는 질문

**Q. hdw1이 죽으면 어떻게 되나?**

hdw1에서 실행 중인 쿼리는 실패합니다. 하지만 hdw2나 hdw3에 새로 접속하면 정상 동작합니다. StateStore가 장애를 감지하고 나머지 Daemon들에게 알리기 때문입니다.

**Q. Catalog Server가 죽으면 어떻게 되나?**

이미 실행 중인 쿼리는 영향 없습니다. 하지만 새 테이블을 만들거나 스키마를 변경해도 Daemon들이 인식하지 못합니다.

**Q. 데이터가 많을수록 빨라지나?**

노드가 많을수록 병렬 처리가 늘어나서 빨라집니다. hdw1, hdw2, hdw3 세 노드가 동시에 처리하면 이론상 1개 노드보다 3배 빠릅니다.
