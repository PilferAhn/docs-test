# Apache Airflow — 워크플로우 오케스트레이션 엔진

> Apache Software Foundation 오픈소스 프로젝트 | 최초 릴리즈: 2015년 (Airbnb 개발)

---

## 한 줄 정의

**코드로 작성한 워크플로우(DAG)를 스케줄링하고 모니터링하는 플랫폼**

---

## 핵심 개념

### DAG (Directed Acyclic Graph)
- 작업(Task)의 실행 순서를 정의한 파이프라인
- Python 코드로 작성
- 방향이 있고 순환하지 않는 그래프 구조

```
Task A → Task B → Task D
       ↘ Task C ↗
```

### Task
- DAG 안의 실행 단위 하나
- BashOperator, PythonOperator, SparkSubmitOperator 등 Operator로 정의

### Operator
- Task가 실제로 무엇을 할지 결정하는 템플릿

| Operator | 하는 일 |
|:---|:---|
| `BashOperator` | Shell 명령 실행 |
| `PythonOperator` | Python 함수 실행 |
| `SparkSubmitOperator` | Spark Job 제출 |
| `PostgresOperator` | SQL 실행 |
| `HttpOperator` | HTTP 요청 |

---

## 아키텍처

```
[Web Server]   ← UI (DAG 모니터링, 실행 이력)
[Scheduler]    ← DAG 파일 읽고 Task 스케줄링
[Executor]     ← Task 실행 방식 결정
[Worker]       ← 실제 Task 실행 (CeleryExecutor 사용 시)
[Metadata DB]  ← DAG/Task 상태 저장 (PostgreSQL)
[Broker]       ← Scheduler ↔ Worker 메시지 전달 (Redis)
```

---

## Executor 종류

| Executor | 병렬 실행 | 용도 |
|:---|:---:|:---|
| `SequentialExecutor` | ❌ | 로컬 개발/테스트 |
| `LocalExecutor` | ✅ | 단일 서버 운영 |
| `CeleryExecutor` | ✅ | 분산 운영 (Worker 여러 대) |
| `KubernetesExecutor` | ✅ | Kubernetes 환경 |

---

## 스케줄 표현식 (cron)

```python
schedule_interval=None            # 수동 실행만
schedule_interval="@daily"        # 매일 자정
schedule_interval="@hourly"       # 매 시간
schedule_interval="0 2 * * *"     # 매일 새벽 2시
schedule_interval="0 9 * * 1-5"   # 평일 오전 9시
schedule_interval="0 */6 * * *"   # 6시간마다
```

---

## Oozie와 비교

| 항목 | Oozie | Airflow |
|:---|:---|:---|
| 워크플로우 정의 | XML | Python 코드 |
| 모니터링 UI | 기본적 | 풍부한 Web UI |
| 스케줄링 | Coordinator | Scheduler |
| 확장성 | Hadoop 종속 | 독립적 |
| 학습 난이도 | 높음 | 낮음 |

---

## 주요 사용 사례

- 데이터 파이프라인 (ETL/ELT) 자동화
- ML 모델 학습 파이프라인
- 리포트 생성 배치
- 데이터 품질 검증
