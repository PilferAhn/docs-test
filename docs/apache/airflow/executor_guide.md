# Airflow Executor 가이드

> Executor는 Airflow가 Task를 어떻게 실행할지 결정하는 핵심 설정

---

## Executor 종류 비교

| 항목 | SequentialExecutor | CeleryExecutor |
|:---|:---|:---|
| 병렬 실행 | ❌ 불가 (한 번에 Task 1개) | ✅ 가능 (여러 Worker) |
| 사용 DB | SQLite 가능 | PostgreSQL / MySQL 필수 |
| Worker 서버 | 단일 서버 | 여러 서버로 확장 가능 |
| 메시지 브로커 | 불필요 | Redis 또는 RabbitMQ 필요 |
| 용도 | 로컬 테스트 / 개발용 | 운영 환경 |
| 설정 난이도 | 쉬움 | 복잡 |

---

## SequentialExecutor

```ini
# airflow.cfg
[core]
executor = SequentialExecutor
```

- Airflow 설치 직후 **기본값**
- Task를 순서대로 하나씩 실행
- DAG 안에 Task가 여러 개여도 동시에 실행되지 않음
- SQLite와 함께 쓸 수 있어서 별도 DB 설정 없이 바로 시작 가능
- **운영 환경에서는 사용하지 않음**

---

## CeleryExecutor

```ini
# airflow.cfg
[core]
executor = CeleryExecutor

[celery]
broker_url = redis://localhost:6379/0
result_backend = db+postgresql://airflow:Dd98969321$9@localhost:5432/airflow
```

- Task를 Celery Worker에게 분산해서 실행
- Worker를 여러 서버에 띄워서 수평 확장 가능
- **브로커(Redis 등) + PostgreSQL DB 필수**
- 운영 환경 표준 구성

### 필요한 구성 요소

```
Scheduler ──→ [Redis 브로커] ──→ Worker 1
                              ──→ Worker 2
                              ──→ Worker 3
                    ↓
              [PostgreSQL]  ← Task 상태 저장
```

### Worker 실행

```bash
# Worker 시작
airflow celery worker

# Flower (Worker 모니터링 UI, 기본 포트 5555)
airflow celery flower
```

---

## 언제 무엇을 쓸까

```
로컬 개발 / 기능 테스트   →  SequentialExecutor
운영 / 병렬 처리 필요     →  CeleryExecutor
```
