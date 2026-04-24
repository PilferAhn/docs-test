# 분산처리 개념 정리

> MapReduce, Spark, 그리고 직접 구현한 Pull 방식 분산처리 비교

---

## 1. MapReduce란

**대량의 데이터를 Map(분류)과 Reduce(집계) 두 단계로 나눠 병렬 처리하는 프레임워크**

```
데이터 10억개
    ↓ Map
Worker 40대가 나눠서 처리
    ↓ Reduce
결과 합치기
```

### 동작 방식 (Push)

```
Master  →  "너는 1번~2500만번 해"  →  Worker 1
Master  →  "너는 2500만~5000만번"  →  Worker 2
...
→ Master가 강제로 나눠줌
```

### 한계

```
- 모든 Worker 스펙이 동일해야 함
- 시작할때 데이터가 전부 있어야 함 (배치 전용)
- 실시간 데이터 유입 불가
- Task마다 요구 스펙이 다르면 맞지 않음
```

---

## 2. MapReduce vs SQL

개념이 거의 같습니다:

```
SQL GROUP BY  =  MapReduce Reduce
SQL WHERE     =  MapReduce Map (필터)
SQL 분산쿼리  =  MapReduce Worker 분배
```

---

## 3. MapReduce와 Spark의 관계

Spark은 MapReduce의 단점을 해결하려고 만든 것입니다.

```
MapReduce 단점        Spark 해결
─────────────────────────────────
디스크 기반  →  메모리 기반 (최대 100배 빠름)
느림         →  빠름
배치만 됨    →  실시간도 됨 (Spark Streaming)
Java만 됨    →  Python, Scala, R 지원
단순한 API   →  DataFrame, SQL 지원
```

```
MapReduce  →  아버지
Spark      →  아버지 단점 보완한 아들
```

현재 Hadoop 클러스터에서 MapReduce 대신 Spark을 올려서 쓰는 게 표준입니다.

---

## 4. MapReduce 현재 위상

```
2004년  Google MapReduce 논문
2006년  Hadoop MapReduce 출시
2014년  Spark 출시 → MapReduce 급격히 감소
현재    새로 MapReduce로 짜는 곳은 거의 없음 (레거시 수준)
```

배워야 하는 이유:

```
Spark, Flink, Kafka 전부 MapReduce 개념 위에서 만들어짐
→ 개념 모르면 Spark이 왜 이렇게 동작하는지 이해 못함
→ 수학으로 치면 미적분보다 극한 개념
```

---

## 5. 직접 구현한 시스템 vs MapReduce

### 직접 구현한 시스템 (Pull 방식)

```python
# Solver가 자기 스펙에 맞는 Task를 직접 골라감
def get_solver_task_id_by_gpu(use_gpu, support_model, ...):
    q = select(Task.task_id).where(
        Task.use_gpu == use_gpu,
        SubTask.model.in_(support_model)
    )
```

```
Worker(Solver)  →  "일 줘"  →  Master(DB)
Worker(Solver)  ←  "여기"  ←  Master(DB)
→ Worker가 자기 스펙에 맞는 Task 골라감
→ 24시간 끝없이 실행되는 서비스
```

### MapReduce (Push 방식)

```
Master  →  Task 전부 확인
        →  Worker에게 강제 배분
        →  처리 완료
        →  종료
→ 명확한 시작과 끝이 있는 배치작업
```

---

## 6. 직접 구현한 시스템이 MapReduce보다 나은 이유

| 상황 | 직접 구현 | MapReduce |
|:---|:---:|:---:|
| Solver 스펙이 제각각 | ✅ | ❌ |
| Task마다 요구 스펙 다름 | ✅ | ❌ |
| 실시간 Task 유입 | ✅ | ❌ |
| 24시간 서비스 | ✅ | ❌ |
| 대용량 배치 처리 | △ | ✅ |

---

## 7. Pull vs Push

```
Pull (직접 구현한 시스템)       Push (MapReduce)
────────────────────────────────────────────
Worker가 일 가져감               Master가 일 나눠줌
실시간 대응 가능                 시작할때 한번만 배분
스펙 달라도 됨                   스펙 동일해야 함
DB 접속 잦음                     DB 접속 최소화
서비스에 적합                    배치에 적합
```

현대 클라우드 시스템 대부분이 Pull 방식입니다:

```
Kubernetes   →  Pull
Docker Swarm →  Pull
AWS SQS      →  Pull
Celery       →  Pull
```

---

## 8. 각 기술의 적합한 용도

```
데이터 미리 쌓아두고 한방에 처리  →  Spark / MapReduce
실시간으로 들어오는 데이터 처리   →  Kafka / Flink / Spark Streaming
스펙/난이도 제각각인 Task 처리    →  직접 구현한 Pull 방식
```

---

## 9. Spark 배우는 순서

```
1. MapReduce 개념 이해  ← 완료
2. Spark 기본 (RDD, DataFrame)
3. Spark SQL
4. Spark Streaming (실시간)
5. 실무 프로젝트
```

### 이미 이해한 개념

```
✅ 분산처리가 왜 필요한지
✅ 병목이 어디서 생기는지
✅ Push vs Pull 차이
✅ 배치 vs 실시간 차이
✅ Master / Worker 역할
✅ DB가 병목이 되는 시점
```

직접 구현한 경험이 있기 때문에 Spark 배울 때 개념이 바로 연결됩니다.
