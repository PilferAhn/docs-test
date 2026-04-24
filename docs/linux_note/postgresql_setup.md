# PostgreSQL 초기 설정 가이드

> 연습용 서버 기준 — Airflow 연동을 위한 PostgreSQL Role/DB 생성

---

## 접속 정보

| 항목 | 값 |
|:---|:---|
| DB 호스트 | localhost |
| 포트 | 5432 |
| postgres 관리자 계정 | `postgres` |
| airflow DB 유저 | `airflow` |
| airflow DB 유저 비밀번호 | `Dd98969321$9` |
| airflow DB 이름 | `airflow` |

---

## 1. postgres 유저로 접속

```bash
# root 에서 postgres 유저로 전환
su - postgres

# psql 실행
psql
```

---

## 2. Airflow용 Role 및 DB 생성

```sql
-- airflow 로그인 role 생성
create role airflow login password 'Dd98969321$9';

-- airflow DB 생성
create database airflow owner airflow encoding 'utf-8';

-- 확인
\du          -- role 목록
\l           -- DB 목록

-- 종료
\q
```

---

## 3. Airflow DB 연결 문자열

```
postgresql+psycopg2://airflow:Dd98969321$9@localhost:5432/airflow
```

`airflow.cfg` 또는 환경변수에 아래와 같이 설정합니다.

```ini
[database]
sql_alchemy_conn = postgresql+psycopg2://airflow:Dd98969321$9@localhost:5432/airflow
```
