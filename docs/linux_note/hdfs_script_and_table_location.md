# HDFS 스크립트 실행 & 테이블 LOCATION 개념

> 실습 중 자주 막히는 두 가지: "HDFS에서 스크립트 어떻게 실행하나", "LOCATION에 파일 하나만 못 쓰나"

---

## 1. HDFS에서 스크립트를 직접 실행할 수 없는 이유

### HDFS는 저장소일 뿐

```
Linux 로컬 파일시스템   →  읽기 / 쓰기 / 실행 모두 가능
HDFS                   →  읽기 / 쓰기 / 삭제만 가능, 실행 기능 없음
```

HDFS는 파일을 저장하는 창고입니다. 창고 안에서 물건을 직접 "작동"시킬 수는 없고, 꺼내서 써야 합니다.

```bash
# 불가능 — HDFS는 실행 개념 자체가 없음
hdfs dfs -exec /user/root/traffic_demo/oozie/workflow/20_create_bronze.sh  # 이런 명령어 없음

# 가능 — 로컬로 내려받은 뒤 실행
hdfs dfs -get /user/root/traffic_demo/oozie/workflow/20_create_bronze.sh /tmp/
chmod +x /tmp/20_create_bronze.sh
bash /tmp/20_create_bronze.sh
```

---

## 2. 다운로드 없이 바로 실행하는 방법

`hdfs dfs -cat`으로 내용을 읽어서 `bash`에 바로 넘기면 됩니다.

```bash
hdfs dfs -cat /user/root/traffic_demo/oozie/workflow/20_create_bronze.sh | bash
```

```
흐름:
hdfs dfs -cat  →  HDFS 파일 내용을 stdout으로 출력
      |        →  파이프: 앞 명령의 출력을 뒤 명령의 입력으로 연결
    bash        →  stdin으로 받은 내용을 스크립트처럼 실행
```

### 주의사항

```bash
# 변수 치환이 있는 스크립트는 그대로 넘기면 오작동할 수 있음
# 예: $FILE_MONTH 같은 변수가 shell에서 먼저 해석됨

# 안전한 방법: 먼저 내려받고 실행
hdfs dfs -get /경로/스크립트.sh /tmp/
bash /tmp/스크립트.sh 2024-01
```

---

## 3. Hive/Impala LOCATION은 왜 디렉토리만 받나

### 실패 예시

```sql
-- ❌ 파일 경로를 직접 쓰면 오류
CREATE EXTERNAL TABLE traffic_demo.traffic_volume
  STORED AS PARQUET
  LOCATION '/user/root/traffic_demo/input/traffic_volume.snappy.parquet';

-- 오류: Path is not a directory: .../traffic_volume.snappy.parquet
```

```sql
-- ✅ 디렉토리 경로를 써야 함
CREATE EXTERNAL TABLE traffic_demo.traffic_volume
  STORED AS PARQUET
  LOCATION '/user/root/traffic_demo/input/';
```

### 왜 디렉토리만 받나 — 분산 처리 설계 때문

Hive/Impala는 처음부터 **"테이블 = 디렉토리"** 로 설계됐습니다.

대용량 데이터를 처리할 때 파일 하나로는 여러 노드가 동시에 쓸 수 없습니다. 그래서 각 노드가 자기 파일을 하나씩 씁니다.

```
/input/
  ├── part-00000.parquet   ← 노드 1이 쓴 파일
  ├── part-00001.parquet   ← 노드 2가 쓴 파일
  ├── part-00002.parquet   ← 노드 3가 쓴 파일
  └── part-00003.parquet   ← 노드 4가 쓴 파일
```

Hive/Impala는 이 폴더를 통째로 읽어서 하나의 테이블처럼 합칩니다.
파일이 1개든 100개든 **폴더를 가리키기만 하면** 알아서 전부 읽습니다.

```
SQL Server  →  DB 엔진이 파일을 내부에서 알아서 관리, 사용자에게 안 보임
Hive/Impala →  HDFS 파일을 직접 다루기 때문에 이 구조가 그대로 노출됨
```

---

## 4. 폴더에 파일이 여러 개면 다 읽힌다

```
/input/
  ├── traffic_volume.snappy.parquet   ← 읽힘
  ├── other_data.parquet              ← 같이 읽힘 ⚠️
  └── temp_file.parquet               ← 같이 읽힘 ⚠️
```

LOCATION이 `/input/`이면 안의 파일을 **전부** 테이블 데이터로 읽습니다.
원하는 파일 하나만 읽게 하려면 **전용 폴더**를 만들어야 합니다.

```bash
# 해결: 파일 전용 폴더 만들기
hdfs dfs -mkdir -p /user/root/traffic_demo/input/traffic_volume/
hdfs dfs -put -f traffic_volume.snappy.parquet /user/root/traffic_demo/input/traffic_volume/

# 이제 LOCATION이 이 폴더만 가리키면 이 파일 하나만 읽음
```

```sql
CREATE EXTERNAL TABLE traffic_demo.traffic_volume
  STORED AS PARQUET
  LOCATION '/user/root/traffic_demo/input/traffic_volume/';
--                                        ↑ 파일 전용 폴더
```

---

## 5. 정리

| 상황 | 방법 |
|:---|:---|
| HDFS 스크립트 실행 | `hdfs dfs -cat 경로 \| bash` |
| 스크립트 내려받아 실행 | `hdfs dfs -get 경로 /tmp/ && bash /tmp/스크립트.sh` |
| LOCATION에 파일 하나만 | 불가능 — 전용 폴더 만들어서 그 폴더를 LOCATION으로 지정 |
| LOCATION 폴더에 파일 여러 개 | 전부 읽힘, 원하는 파일만 있는 전용 폴더 사용 권장 |
