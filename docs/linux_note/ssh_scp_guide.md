# SSH / SCP 실무 가이드

> 서버 접속, 파일 전송, 키 인증까지 실무에서 자주 쓰는 패턴 정리

---

## 목차

1. [SSH 기본 접속](#1-ssh-기본-접속)
2. [SSH 키 공유 (비번 없이 접속)](#2-ssh-키-공유-비번-없이-접속)
3. [SCP 파일 전송](#3-scp-파일-전송)
4. [SSH 설정 파일 (~/.ssh/config)](#4-ssh-설정-파일-sshconfig)
5. [SSH 터널링 / 포트포워딩](#5-ssh-터널링--포트포워딩)
6. [자주 쓰는 SSH 옵션](#6-자주-쓰는-ssh-옵션)
7. [에러 모음](#7-에러-모음)

---

## 1. SSH 기본 접속

```bash
# 기본 접속
ssh user@서버IP

# 포트 지정 (기본 22)
ssh -p 2222 user@서버IP

# 접속 끊기
exit
```

---

## 2. SSH 키 공유 (비번 없이 접속)

### 원리

```
내 컴퓨터  →  공개키(자물쇠) 서버에 등록
내 컴퓨터  →  개인키(열쇠) 내가 보관

접속할 때
서버: "이 자물쇠 열 수 있어?"
내 컴퓨터: 개인키로 열어버림
→ 비번 없이 통과
```

### 파일 위치

```
~/.ssh/id_rsa        개인키 (절대 공유 X)
~/.ssh/id_rsa.pub    공개키 (서버에 등록하는 것)
~/.ssh/known_hosts   접속한 서버 목록
~/.ssh/authorized_keys  서버에서: 허용된 공개키 목록
```

### 설정 방법

**1단계: 키 생성**

```bash
ssh-keygen -t rsa -b 4096

# 물어보는 것들
Enter file:       그냥 엔터 (기본 경로 사용)
Enter passphrase: 그냥 엔터 (비번 없이)
```

**2단계: 서버에 공개키 등록**

```bash
# Linux / Mac
ssh-copy-id user@서버IP

# Windows PowerShell (ssh-copy-id 없음)
type $env:USERPROFILE\.ssh\id_rsa.pub | ssh user@서버IP "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

**명령어 해설 (Windows)**

```
type $env:USERPROFILE\.ssh\id_rsa.pub
→ 내 공개키 파일 내용 출력
  $env:USERPROFILE = C:\Users\내계정
  id_rsa.pub = 공개키 파일

| (파이프)
→ 왼쪽 출력을 오른쪽 입력으로 넘김

ssh user@서버IP "..."
→ 서버에 접속해서 따옴표 안의 명령어 실행

mkdir -p ~/.ssh
→ .ssh 폴더 없으면 생성

cat >> ~/.ssh/authorized_keys
→ 넘어온 공개키를 허용 목록에 추가
```

**3단계: 확인**

```bash
# 비번 없이 접속되면 성공
ssh user@서버IP
```

---

## 3. SCP 파일 전송

### 기본 문법

```
scp [옵션] 출발지 목적지
```

### 내 컴퓨터 → 서버 (업로드)

```bash
# 파일 하나
scp ./file.txt user@서버IP:/tmp/

# 폴더 통째로
scp -r ./myfolder user@서버IP:/tmp/

# 포트 지정
scp -P 2222 ./file.txt user@서버IP:/tmp/
```

### 서버 → 내 컴퓨터 (다운로드)

```bash
# 파일 하나
scp user@서버IP:/tmp/file.txt ./

# 폴더 통째로
scp -r user@서버IP:/tmp/myfolder ./

# 현재 폴더에 받기
scp user@서버IP:/path/to/file.parquet .
```

### SCP vs SFTP 비교

```
SCP   →  명령어 한 줄로 파일 전송 (빠름, 스크립트에 적합)
SFTP  →  FTP처럼 대화형으로 파일 탐색 + 전송 (파일 여러 개 관리 편함)
```

```bash
# SFTP 접속
sftp user@서버IP

# SFTP 안에서
ls          서버 파일 목록
lls         내 컴퓨터 파일 목록
get file    서버 → 내 컴퓨터
put file    내 컴퓨터 → 서버
exit        종료
```

---

## 4. SSH 설정 파일 (~/.ssh/config)

서버 정보를 저장해두면 매번 IP/포트 안 써도 됩니다.

### 설정 파일 만들기

```bash
vi ~/.ssh/config
```

```
Host cloudera
    HostName 10.0.1.171
    User root
    Port 22
    IdentityFile ~/.ssh/id_rsa

Host dev-server
    HostName 10.0.1.200
    User ubuntu
    Port 2222
```

### 사용

```bash
# 전: ssh root@10.0.1.171
# 후:
ssh cloudera

# SCP도 동일
scp cloudera:/tmp/file.txt ./
```

---

## 5. SSH 터널링 / 포트포워딩

서버 내부 포트를 내 컴퓨터에서 접근할 때 씁니다.

```bash
# 로컬 포트 8888 → 서버의 localhost:8888 연결
ssh -L 8888:localhost:8888 user@서버IP

# 백그라운드로 실행 (-N: 명령 실행 안함, -f: 백그라운드)
ssh -NfL 8888:localhost:8888 user@서버IP
```

### 언제 쓰나

```
Jupyter Notebook 서버 내부에서 실행
→ 내 브라우저에서 localhost:8888 접속

Cloudera Manager 웹 UI
→ 서버 내부 포트를 내 컴퓨터로 포워딩
```

---

## 6. 자주 쓰는 SSH 옵션

| 옵션 | 의미 | 예시 |
|:---|:---|:---|
| `-p` | 포트 지정 | `ssh -p 2222 user@IP` |
| `-i` | 개인키 파일 지정 | `ssh -i ~/.ssh/my_key user@IP` |
| `-L` | 로컬 포트포워딩 | `ssh -L 8080:localhost:8080 user@IP` |
| `-N` | 명령 실행 없이 터널만 | `ssh -NL 8080:...` |
| `-f` | 백그라운드 실행 | `ssh -Nf ...` |
| `-v` | 디버그 출력 (접속 안 될 때) | `ssh -v user@IP` |
| `-o StrictHostKeyChecking=no` | 호스트 키 확인 스킵 | 자동화 스크립트에서 |

---

## 7. 에러 모음

| 에러 | 원인 | 해결 |
|:---|:---|:---|
| `Connection refused` | SSH 서비스 꺼져있음 또는 포트 다름 | 포트 확인, 서버 상태 확인 |
| `Permission denied (publickey)` | 공개키 등록 안 됨 또는 권한 문제 | 키 등록 다시, `chmod 600 ~/.ssh/authorized_keys` |
| `Host key verification failed` | 서버 키가 바뀜 (재설치 등) | `ssh-keygen -R 서버IP` |
| `WARNING: UNPROTECTED PRIVATE KEY` | 개인키 권한이 너무 열려있음 | `chmod 600 ~/.ssh/id_rsa` |
| `ssh-copy-id not found` | Windows에는 없는 명령어 | 위 Windows 수동 방법 사용 |

---

## 한눈에 보기

```
처음 설정
ssh-keygen                          키 생성
ssh-copy-id user@IP                 공개키 등록 (Linux/Mac)
type id_rsa.pub | ssh user@IP ...   공개키 등록 (Windows)

접속
ssh user@IP                         기본 접속
ssh -p 2222 user@IP                 포트 지정
ssh cloudera                        config 별칭 사용

파일 전송
scp file.txt user@IP:/tmp/          업로드
scp user@IP:/tmp/file.txt ./        다운로드
scp -r folder user@IP:/tmp/         폴더 업로드
```
