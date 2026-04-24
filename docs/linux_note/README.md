# Things to Know About Linux & HDFS

> Cloudera 실습 중 자주 마주치는 명령어들을 정리한 노트

---

## 1. 리눅스 기본 명령어

### 파일/폴더 탐색

```bash
ls          # 현재 폴더 목록
ls -l       # 상세 목록 (권한, 크기, 날짜)
ls -lh      # 상세 목록 + 파일 크기 사람이 읽기 쉽게 (KB, MB)
pwd         # 지금 내가 어느 폴더에 있는지
cd /tmp     # /tmp 폴더로 이동
cd ~        # 홈 폴더로 이동
```

### 파일/폴더 생성·복사·삭제

```bash
mkdir 폴더명           # 폴더 생성
mkdir -p a/b/c        # 중간 폴더 없어도 한번에 생성 (-p = parents)
cp a.txt /tmp/        # 파일 복사
mv a.txt /tmp/        # 파일 이동 (잘라내기)
rm a.txt              # 파일 삭제
rm -rf 폴더명         # 폴더 통째로 삭제 (-r = recursive, -f = force)
```

### 파일 내용 확인

```bash
cat file.txt          # 파일 전체 출력
head -10 file.txt     # 앞 10줄만 출력
tail -10 file.txt     # 뒤 10줄만 출력
```

### 파일 전송

```bash
# 로컬 → 서버로 보내기
scp 파일명 계정@서버IP:/tmp/

# 서버 → 로컬로 받기
scp 계정@서버IP:/tmp/파일명 ./
```

---

## 2. 옵션 읽는 법

명령어 뒤에 `-` 로 시작하는 것들이 옵션입니다.

```bash
mkdir -p /a/b/c
#        ↑
#        옵션: p = parents (부모 폴더도 함께 생성)

hdfs dfs -put -f file.parquet /hdfs/path/
#              ↑
#              옵션: f = force (이미 있어도 덮어쓰기)
```

| 자주 쓰는 옵션 | 의미 |
|:---|:---|
| `-p` | parents — 중간 경로 없어도 한번에 생성 |
| `-f` | force — 강제로 실행 (덮어쓰기, 묻지 않음) |
| `-r` | recursive — 하위 폴더까지 모두 |
| `-h` | human-readable — 사람이 읽기 쉬운 단위(KB, MB) |
| `-l` | long — 상세 정보 출력 |

---

## 2-1. `-h` 옵션 제대로 이해하기

### 왜 `-h`를 쓰는가?

원래 디스크 용량은 **바이트 단위 숫자**로 출력됩니다.
사람이 읽기 불편하니까 `-h`를 붙이면 **KB / MB / GB** 단위로 변환해서 보여줍니다.

```bash
# -h 없이 df 실행 → 숫자가 날것으로 나옴
$ df
Filesystem     1K-blocks    Used Available Use%
/dev/sda1       52428800 1234567  51194233   3%

# -h 붙이면 → 사람이 읽기 편한 단위로 나옴
$ df -h
Filesystem      Size  Used Avail Use%
/dev/sda1        50G  1.2G   49G   3%
```

### `-h`가 human-readable로 **되는** 명령어

```bash
df -h          # 디스크 사용량 (파티션별)
du -h 파일명   # 파일/폴더 크기
du -sh 폴더명  # 폴더 전체 크기 합산 (-s = summary)
ls -lh         # 파일 목록 + 크기 단위 변환
free -h        # 메모리 사용량
hdfs dfs -du -h /경로/   # HDFS 용량
```

### `-h`가 **다른 의미**로 쓰이는 명령어 ⚠️

| 명령어 | `-h`의 의미 | 비고 |
|:---|:---|:---|
| `grep -h` | hide filename — 파일명 숨기기 | human-readable 아님 |
| `ps -h` | hide header — 헤더 줄 숨기기 | human-readable 아님 |
| `git -h` | help — 도움말 출력 | `--help`와 동일 |
| `python -h` | help — 도움말 출력 | `--help`와 동일 |
| `rm -h` | 오류 — 해당 옵션 없음 | 사용 불가 |

> **결론:** `-h`는 용량 관련 명령어(`df`, `du`, `ls`, `free`)에서만 human-readable로 쓰입니다.
> 다른 명령어는 `man <명령어>` 또는 `<명령어> --help`로 확인하는 게 안전합니다.

---

## 2-2. 헷갈리기 쉬운 옵션 비교

같은 알파벳이라도 **명령어마다 의미가 다른** 경우가 많습니다.

### `-r` 옵션

| 명령어 | `-r`의 의미 |
|:---|:---|
| `rm -r` | recursive — 하위 폴더까지 모두 삭제 |
| `cp -r` | recursive — 폴더 통째로 복사 |
| `grep -r` | recursive — 하위 폴더까지 검색 |
| `scp -r` | recursive — 폴더 통째로 전송 |

```bash
# 폴더 복사할 때는 -r 필수
cp -r /tmp/myfolder /backup/

# 폴더 안에서 특정 단어 검색
grep -r "error" /var/log/
```

### `-f` 옵션

| 명령어 | `-f`의 의미 |
|:---|:---|
| `rm -f` | force — 확인 없이 강제 삭제 |
| `hdfs dfs -put -f` | force — 이미 있는 파일 덮어쓰기 |
| `cp -f` | force — 대상 파일 있어도 덮어쓰기 |
| `grep -F` | fixed-string — 정규식 아닌 문자열 그대로 검색 |

### `-v` 옵션

| 명령어 | `-v`의 의미 |
|:---|:---|
| `cp -v` | verbose — 복사하면서 어떤 파일 처리하는지 출력 |
| `rm -v` | verbose — 삭제하면서 파일명 출력 |
| `grep -v` | invert — 해당 패턴이 **없는** 줄만 출력 |
| `tar -v` | verbose — 압축/해제 중 파일 목록 출력 |

```bash
# grep -v : 패턴 없는 줄만 → 로그에서 특정 단어 제외
grep -v "DEBUG" app.log     # DEBUG 없는 줄만 출력

# cp -v : 어떤 파일 복사하는지 보면서 진행
cp -rv /tmp/data /backup/
```

### `-n` 옵션

| 명령어 | `-n`의 의미 |
|:---|:---|
| `head -n 20` | 앞에서 20줄만 출력 |
| `tail -n 20` | 뒤에서 20줄만 출력 |
| `grep -n` | line number — 검색 결과에 줄 번호 표시 |

```bash
# 로그 파일에서 "error" 단어가 몇 번째 줄에 있는지 확인
grep -n "error" app.log
# 출력: 42:error connecting to database
#       ↑ 줄 번호
```

### 모르는 옵션은 어떻게 확인하나?

```bash
# 방법 1: --help 옵션 (대부분의 명령어 지원)
df --help
grep --help

# 방법 2: man 페이지 (Manual)
man df
man grep
# 종료는 q 키

# 방법 3: 짧은 도움말
df -h  # 일부 명령어는 -h가 help
```

> **원칙:** 확실하지 않은 옵션은 `--help` 또는 `man`으로 먼저 확인하세요.
> 특히 `-f`(force), `-r`(recursive)처럼 **되돌릴 수 없는 작업**에 붙는 옵션은 더욱 주의!

---

## 3. HDFS 명령어

> `hdfs dfs` = HDFS용 파일 명령어
> 리눅스 명령어와 거의 같은데, 앞에 `hdfs dfs`만 붙이면 됩니다.

### 리눅스 vs HDFS 비교

| 하고 싶은 것 | 리눅스 (로컬) | HDFS |
|:---|:---|:---|
| 폴더 목록 보기 | `ls /tmp` | `hdfs dfs -ls /tmp` |
| 폴더 만들기 | `mkdir /data` | `hdfs dfs -mkdir /data` |
| 파일 올리기 | — | `hdfs dfs -put 파일 /hdfs경로/` |
| 파일 내려받기 | — | `hdfs dfs -get /hdfs경로/파일 ./` |
| 파일 내용 보기 | `cat 파일` | `hdfs dfs -cat /hdfs경로/파일` |
| 파일 삭제 | `rm 파일` | `hdfs dfs -rm /hdfs경로/파일` |
| 폴더 삭제 | `rm -rf 폴더` | `hdfs dfs -rm -r /hdfs경로/폴더` |
| 파일 크기 확인 | `du -sh 파일` | `hdfs dfs -du -h /hdfs경로/` |

### 자주 쓰는 HDFS 명령어 패턴

```bash
# 폴더 만들기 (중간 경로 없어도 OK)
hdfs dfs -mkdir -p /user/root/my_project/input

# 로컬 파일 → HDFS 업로드 (이미 있으면 덮어쓰기)
hdfs dfs -put -f /tmp/data.parquet /user/root/my_project/input/

# HDFS 파일 목록 확인
hdfs dfs -ls /user/root/my_project/input/

# HDFS 파일 내용 확인
hdfs dfs -cat /user/root/my_project/output/result.txt

# HDFS 전체 사용량 확인
hdfs dfs -du -h /user/root/
```

---

## 4. 경로 이해하기

```
/user/root/traffic_demo/input/traffic.parquet
↑     ↑    ↑             ↑    ↑
│     │    │             │    └─ 파일명
│     │    │             └─ 하위 폴더
│     │    └─ 내가 만든 프로젝트 폴더
│     └─ 계정명 (root)
└─ HDFS 최상위 경로
```

리눅스와 동일하게 `/` 로 경로를 구분합니다.

---

## 5. 파일 권한 (chmod)

### 권한이란?

리눅스에서 모든 파일은 **누가 뭘 할 수 있는지** 권한이 정해져 있습니다.

```bash
ls -l 20_create_bronze.sh
# 출력: -rw-r--r-- 1 root root 1234 Apr 22 10:00 20_create_bronze.sh
#       ↑↑↑↑↑↑↑↑↑
#       권한 정보
```

권한 문자 9자리는 3묶음으로 나뉩니다.

```
-  rw-  r--  r--
↑   ↑    ↑    ↑
│   │    │    └─ others  : 그 외 모든 사용자
│   │    └─ group    : 같은 그룹 사용자
│   └─ owner    : 파일 소유자 (나)
└─ 파일 종류 (- = 일반파일, d = 폴더)
```

각 자리의 의미:

```
r = read    (읽기)   : 파일 내용을 볼 수 있음
w = write   (쓰기)   : 파일 내용을 수정할 수 있음
x = execute (실행)   : 파일을 프로그램처럼 실행할 수 있음
- = 해당 권한 없음
```

---

### 왜 shell 스크립트에 `chmod +x`가 필요한가

`.sh` 파일은 텍스트 파일입니다. 리눅스는 텍스트 파일을 기본적으로 실행 불가 상태로 만듭니다.
실행하려면 **실행 권한(x)** 을 직접 부여해야 합니다.

```bash
# 권한 부여 전 → 실행 안 됨
bash 20_create_bronze.sh     # bash로 직접 호출하면 가능
./20_create_bronze.sh        # 이 방식은 Permission denied 에러

# 실행 권한 부여
chmod +x 20_create_bronze.sh

# 이제 직접 실행 가능
./20_create_bronze.sh        # OK
```

---

### chmod 사용법: 기호 방식

```bash
chmod +x 파일명      # 실행 권한 추가 (소유자+그룹+others 모두)
chmod -x 파일명      # 실행 권한 제거
chmod +r 파일명      # 읽기 권한 추가
chmod +w 파일명      # 쓰기 권한 추가

# 대상을 지정할 수도 있음
chmod u+x 파일명     # u = user(소유자)만 실행 권한 추가
chmod g+x 파일명     # g = group만 실행 권한 추가
chmod o+x 파일명     # o = others만 실행 권한 추가
chmod a+x 파일명     # a = all (모두) 실행 권한 추가 → +x 와 동일
```

---

### chmod 사용법: 숫자 방식

권한을 숫자로도 표현할 수 있습니다.

```
r = 4
w = 2
x = 1
- = 0
```

세 자리를 더해서 한 묶음(소유자/그룹/others)의 권한을 표현합니다.

```
rwx = 4+2+1 = 7   (읽기+쓰기+실행)
rw- = 4+2+0 = 6   (읽기+쓰기)
r-x = 4+0+1 = 5   (읽기+실행)
r-- = 4+0+0 = 4   (읽기만)
--- = 0+0+0 = 0   (아무것도 못함)
```

세 묶음을 이어붙이면:

```bash
chmod 755 파일명
#     ↑↑↑
#     │││
#     ││└─ others : r-x = 5 (읽기+실행)
#     │└─ group  : r-x = 5 (읽기+실행)
#     └─ owner  : rwx = 7 (읽기+쓰기+실행)
```

---

### 자주 쓰는 숫자 조합

| 숫자 | 권한 | 의미 | 언제 씀 |
|:---:|:---|:---|:---|
| `755` | `rwxr-xr-x` | 소유자는 모두, 나머지는 읽기+실행 | **shell 스크립트** |
| `644` | `rw-r--r--` | 소유자는 읽기+쓰기, 나머지는 읽기만 | 일반 설정 파일, 데이터 파일 |
| `600` | `rw-------` | 소유자만 읽기+쓰기 | SSH 키, 비밀번호 파일 |
| `777` | `rwxrwxrwx` | 모두가 모든 권한 | ⚠️ 보안상 권장하지 않음 |

```bash
# shell 스크립트 실행 권한 부여 (가장 일반적)
chmod 755 20_create_bronze.sh

# 기호 방식과 동일한 결과
chmod +x 20_create_bronze.sh
```

---

### 이 프로젝트 스크립트에 적용

```bash
# 클러스터에 스크립트 올린 후 실행 권한 일괄 부여
chmod +x /tmp/10_upload.sh
chmod +x /tmp/20_create_bronze.sh
chmod +x /tmp/30_create_silver.sh
chmod +x /tmp/40_save_result.sh
chmod +x /tmp/50_preview.sh

# 한 번에 처리
chmod +x /tmp/*.sh

# 권한 확인
ls -l /tmp/*.sh
# 출력:
# -rwxr-xr-x 1 root root ... 10_upload.sh
# -rwxr-xr-x 1 root root ... 20_create_bronze.sh
# ...
```

---

## 6. 에러가 날 때

| 에러 메시지 | 원인 | 해결 |
|:---|:---|:---|
| `No such file or directory` | 경로가 없음 | `mkdir -p`로 먼저 생성 |
| `File exists` | 이미 파일 있음 | `-f` 옵션 추가 |
| `Permission denied` | 권한 없음 | `chmod +x` 또는 `sudo` |
| `Connection refused` | 서버 꺼져있음 | 서버 상태 확인 |
