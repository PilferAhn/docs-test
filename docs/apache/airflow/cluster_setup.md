# traffic_demo_airflow

Cloudera 엣지 노드에서 Oozie 워크플로우를 Airflow DAG으로 전환하는 프로젝트

---

## 프로젝트 개요

기존 Oozie 기반의 교통량(traffic volume) 데이터 처리 파이프라인을 Apache Airflow로 재구성한다.

---

## 클러스터 구성

| 서버 | 역할 |
|------|------|
| adm1 | Airflow Scheduler, PostgreSQL, Redis, NFS Server |
| hdw1 | Airflow Celery Worker, NFS Client |
| hdw2 | Airflow Celery Worker, NFS Client |
| hdw3 | Airflow Celery Worker, NFS Client |

---

## 디렉토리 구조

```
/root/airflow/                        # AIRFLOW_HOME
├── airflow.cfg                       # Airflow 설정 파일
├── airflow.db                        # (사용 안 함, PostgreSQL로 대체)
├── dags/                             # DAG 파일 위치 (NFS 공유)
│   └── traffic_demo_dag.py
├── logs/
├── scripts/                          # 참조용 스크립트 사본
├── start_airflow.sh                  # 전체 시작 스크립트
└── stop_airflow.sh                   # 전체 종료 스크립트

/root/traffic_demo/airflow/scripts/   # 실제 sh 스크립트 위치
├── 10_upload.sh
├── 20_create_table_impala.sh
├── 21_create_table_hive.sh
├── 22_create_table_spark.sh
├── 30_bronze_to_silver_impala.sh
├── 31_bronze_to_silver_hive.sh
├── 32_bronze_to_silver_spark.sh
├── 50_save_result.sh
└── 50_save_result_impala.sh
```

---

## 데이터 파이프라인

```
10_upload → 20_create_table_impala → 30_bronze_to_silver_impala → 50_save_result_impala
```

| 스크립트 | 역할 |
|----------|------|
| `10_upload.sh` | 로컬 Parquet → HDFS input 업로드 (멱등성 보장) |
| `20_create_table_impala.sh` | Impala External Table 생성 (bronze) |
| `30_bronze_to_silver_impala.sh` | bronze → silver 변환 + DQ 검증 |
| `50_save_result_impala.sh` | silver row count → HDFS output 저장 |

### HDFS 경로

| 구분 | 경로 |
|------|------|
| 입력 | `/user/root/traffic_demo/input/traffic_volume_bronze` |
| 출력 | `/user/root/traffic_demo/output/count_result.txt` |
| Oozie(기존) | `/user/root/traffic_demo/oozie/workflow/` |

---

## Airflow 설치 정보

| 항목 | 값 |
|------|----|
| AIRFLOW_HOME | `/root/airflow` |
| Airflow Version | `2.8.4` |
| Python | `3.9.18` |
| Executor | `CeleryExecutor` |
| PostgreSQL | `adm1:5432` / DB: `airflow` / User: `airflow` / PW: `Dd98969321$9` |
| Redis | `adm1:6379` |
| NFS 공유 경로 | `adm1:/root/airflow/dags` |

### airflow.cfg 주요 설정

```ini
[core]
executor = CeleryExecutor
sql_alchemy_conn = postgresql+psycopg2://airflow:Dd98969321$9@adm1:5432/airflow

[celery]
broker_url = redis://adm1:6379/0
result_backend = db+postgresql+psycopg2://airflow:Dd98969321$9@adm1:5432/airflow
worker_concurrency = 4
```

---

## 시작 / 종료

```bash
# 전체 시작 (adm1에서 실행)
/root/airflow/start_airflow.sh

# 전체 종료 (adm1에서 실행)
/root/airflow/stop_airflow.sh
```

## DAG 실행 (터미널)

```bash
export AIRFLOW_HOME=/root/airflow

# DAG 목록 확인
airflow dags list

# DAG 실행
airflow dags trigger traffic_demo

# 실행 상태 확인
airflow dags list-runs -d traffic_demo

# Task 상태 확인
airflow tasks states-for-dag-run traffic_demo <run_id>

# Task 로그 확인
airflow tasks logs traffic_demo 10_upload <run_id>
```

---

## Troubleshooting

### 1. HDFS 스크립트 복사

**문제:** Oozie 워크플로우 스크립트가 HDFS에 있어서 Airflow에서 직접 참조 불가

**해결:** HDFS → 로컬로 복사 (HDFS 원본은 유지)

```bash
hdfs dfs -get /user/root/traffic_demo/oozie/workflow/*.sh /root/traffic_demo/airflow/scripts/
```

---

### 2. PostgreSQL 접속 불가

**문제:** `pg_hba.conf`가 모든 연결에 `md5` 인증을 요구하는데 postgres 비밀번호를 몰랐음

```
sudo -u postgres psql  →  Password for user postgres: (실패)
```

**원인:** PostgreSQL이 Cloudera 설치 시 자동 설치됨 (2026-01-22). 비밀번호 불명

**해결:** Cloudera 설정 파일에서 scm 계정 정보 확인 후, OS 계정으로 전환하여 접속

```bash
# Cloudera DB 계정 확인
cat /etc/cloudera-scm-server/db.properties
# → user=scm, password=scm

# OS 계정 전환으로 접속
su - postgres
psql
```

```sql
CREATE ROLE airflow LOGIN PASSWORD 'Dd98969321$9';
CREATE DATABASE airflow OWNER airflow ENCODING 'utf-8';
\q
```

---

### 3. Airflow 버전이 자꾸 3.x로 올라가는 문제

**문제:** provider 패키지 설치 시 pip 의존성 해결 과정에서 Airflow가 2.8.4 → 3.0.6으로 자동 업그레이드됨

**원인:** 이전 설치 과정에서 `apache-airflow-core 3.0.6`, `pydantic 2.x` 등 3.x 의존 패키지들이 남아있어 pip가 계속 3.x를 끌어올림

**해결:** airflow 관련 패키지 전체 제거 후 constraints 파일로 버전 고정 재설치

```bash
# 전체 제거
pip3 uninstall apache-airflow apache-airflow-core apache-airflow-task-sdk \
  apache-airflow-providers-common-compat apache-airflow-providers-fab \
  apache-airflow-providers-common-io apache-airflow-providers-common-sql \
  apache-airflow-providers-celery apache-airflow-providers-postgres \
  apache-airflow-providers-smtp apache-airflow-providers-standard -y

# pydantic 2.x 제거 (3.x 의존 패키지)
pip3 uninstall pydantic pydantic-core pydantic-extra-types pydantic-settings -y
pip3 install "pydantic==1.10.14"

# 버전 고정 재설치
pip3 install "apache-airflow[celery,postgres]==2.8.4" \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.8.4/constraints-3.9.txt"
```

**교훈:** 처음부터 venv(가상환경)에 설치했으면 이 문제가 발생하지 않음

---

### 4. Worker에서 `airflow celery` 명령 없음

**문제:** hdw 서버에서 `airflow celery worker` 실행 시 `invalid choice: 'celery'` 오류

**원인:** Worker에 airflow.cfg 복사 시 타이밍 문제로 구버전(SequentialExecutor)이 복사됨. Executor가 SequentialExecutor면 celery 명령이 활성화되지 않음

**해결:** adm1의 최신 airflow.cfg를 다시 복사

```bash
scp /root/airflow/airflow.cfg hdw1:/root/airflow/airflow.cfg
scp /root/airflow/airflow.cfg hdw2:/root/airflow/airflow.cfg
scp /root/airflow/airflow.cfg hdw3:/root/airflow/airflow.cfg
```

---

### 5. Worker에서 PostgreSQL/Redis 연결 실패

**문제:** Worker 시작 시 PostgreSQL 연결 오류

```
connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
```

**원인:** airflow.cfg의 DB/Redis 주소가 `localhost`로 설정되어 있어 Worker가 자기 자신(hdw)에서 PostgreSQL을 찾음. PostgreSQL과 Redis는 adm1에만 있음

**해결:** airflow.cfg에서 `localhost` → `adm1`으로 변경

```ini
sql_alchemy_conn = postgresql+psycopg2://airflow:Dd98969321$9@adm1:5432/airflow
broker_url = redis://adm1:6379/0
result_backend = db+postgresql+psycopg2://airflow:Dd98969321$9@adm1:5432/airflow
```

변경 후 전체 Worker에 재배포

```bash
for h in hdw1 hdw2 hdw3; do
  scp /root/airflow/airflow.cfg $h:/root/airflow/airflow.cfg
done
```

---

## 진행 현황

- [x] HDFS 스크립트 → 로컬 복사
- [x] Airflow 2.8.4 설치 (adm1, hdw1, hdw2, hdw3)
- [x] Redis 설치 및 실행 (adm1)
- [x] PostgreSQL airflow DB/계정 생성
- [x] airflow.cfg 설정 (CeleryExecutor, PostgreSQL, Redis)
- [x] Airflow DB 초기화 (PostgreSQL)
- [x] NFS 설정 (DAG 파일 공유)
- [x] DAG 파일 작성 (`traffic_demo_dag.py`)
- [x] Scheduler 시작 스크립트
- [x] Worker 시작 스크립트
- [ ] DAG 실제 실행 테스트

---

## 서버 간 연결 방법 (SSH / SCP)

> adm1에서 hdw1~hdw3으로 명령을 보내거나 파일을 전송할 때 사용합니다.
> 비밀번호 없이 바로 접속되는 이유는 아래 "SSH 키 인증" 참고.

---

### 1. 단순 SSH 접속 — 원격 서버에서 명령 실행하기

로컬에서 타이핑하지만 실제 명령은 원격 서버(hdw1 등)에서 실행됩니다.

```bash
# hdw1에 접속해서 hostname -I 실행 후 결과를 adm1에서 받아봄
ssh hdw1 "hostname -I"

# 여러 서버에 같은 명령을 순서대로 실행
for h in hdw1 hdw2 hdw3; do
  echo "=== $h ==="
  ssh $h "python3 --version"
done
```

> `for h in hdw1 hdw2 hdw3` : h라는 변수에 hdw1 → hdw2 → hdw3 순서로 넣으면서 반복
> `ssh $h "명령"` : $h 서버에 접속해서 따옴표 안의 명령을 실행

---

### 2. SCP — 파일 전송하기

SCP = Secure Copy. SSH를 이용해서 서버 간 파일을 복사합니다.

```bash
# adm1 → hdw1으로 파일 하나 복사
scp /root/airflow/airflow.cfg hdw1:/root/airflow/airflow.cfg
#   ↑ 보낼 파일 (adm1 경로)    ↑ 받을 서버:경로

# 여러 서버에 동시 배포 (for 루프)
for h in hdw1 hdw2 hdw3; do
  scp /root/airflow/airflow.cfg $h:/root/airflow/airflow.cfg
done

# 스크립트 파일 전송
scp /root/airflow/install_worker.sh hdw1:/tmp/install_worker.sh
```

> `scp 출발지 목적지` 형태입니다.
> 원격 경로는 `서버명:절대경로` 로 씁니다.

---

### 3. SSH로 원격 스크립트 실행하기

파일을 전송한 뒤 바로 그 파일을 원격에서 실행할 수 있습니다.

```bash
# 전송한 스크립트를 hdw1에서 실행
ssh hdw1 "bash /tmp/install_worker.sh"

# 여러 서버에서 순서대로 실행
for h in hdw1 hdw2 hdw3; do
  echo "=== $h 설치 시작 ==="
  ssh $h "bash /tmp/install_worker.sh"
done
```

> `bash /tmp/...` : 스크립트에 실행 권한(chmod +x)이 없어도 bash로 직접 실행 가능

---

### 4. SSH로 환경변수 포함 명령 실행하기

일부 명령은 환경변수가 설정돼 있어야 정상 동작합니다.
따옴표 안에서 `export` 와 명령을 `&&` 로 이어 씁니다.

```bash
# 환경변수 설정 후 Worker 백그라운드 실행
ssh hdw1 "export AIRFLOW_HOME=/root/airflow && airflow celery worker -D"
#                ↑ 환경변수 설정              ↑ -D = 백그라운드(daemon) 실행

# 여러 서버에 Worker 시작
for h in hdw1 hdw2 hdw3; do
  ssh $h "export AIRFLOW_HOME=/root/airflow && airflow celery worker -D"
done
```

> `&&` : 앞 명령이 성공했을 때만 뒤 명령 실행 (앞이 실패하면 멈춤)
> `-D` (daemon) : 터미널을 닫아도 Worker가 계속 실행됨

---

### 5. SSH 접속 확인 — 연결 테스트

서버가 살아있는지 빠르게 확인할 때 씁니다.

```bash
for h in hdw1 hdw2 hdw3; do
  echo -n "$h: "
  ssh -o ConnectTimeout=3 -o BatchMode=yes $h "hostname" 2>&1
done
```

> `-o ConnectTimeout=3` : 3초 안에 응답 없으면 포기 (기본은 무한 대기)
> `-o BatchMode=yes` : 비밀번호 입력 프롬프트 없이 실패 처리 (자동화 스크립트에서 필수)
> `2>&1` : 에러 메시지도 화면에 출력 (실패 원인 확인용)

---

### 이게 가능한 이유 — SSH 키 인증

비밀번호 없이 바로 접속되는 건 **SSH 공개키 인증**이 설정되어 있기 때문입니다.

```
adm1의 id_rsa.pub (공개키)
    → hdw1~hdw3의 ~/.ssh/authorized_keys 에 등록됨
    → adm1에서 hdw로 접속할 때 비밀번호 없이 자동 인증
```

```bash
# adm1의 공개키 확인
cat ~/.ssh/id_rsa.pub

# hdw 서버에서 등록된 키 확인
ssh hdw1 "cat ~/.ssh/authorized_keys"
```

> Cloudera 설치 시 자동으로 키 교환이 설정됩니다.

---

### 호스트명으로 접속되는 이유 — /etc/hosts

IP 대신 `hdw1`, `hdw2`, `hdw3`으로 접속할 수 있는 건 `/etc/hosts`에 등록되어 있기 때문입니다.

```bash
cat /etc/hosts | grep hdw
# 10.0.1.174  hdw1
# 10.0.1.175  hdw2
# 10.0.1.176  hdw3
```

> `/etc/hosts` : DNS 없이 호스트명 → IP를 직접 매핑하는 파일
> Cloudera 클러스터는 설치 시 자동으로 등록됩니다.
