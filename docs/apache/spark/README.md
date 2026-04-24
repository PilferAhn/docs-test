# Apache Spark — 인메모리 분산 처리 엔진

> Apache Software Foundation 오픈소스 프로젝트 | 최초 릴리즈: 2014년 (UC Berkeley AMPLab 개발)

---

## 한 줄 정의

**대규모 데이터를 메모리에 올려서 빠르게 처리하는 분산 컴퓨팅 엔진**

---

## MapReduce와 차이

| 항목 | MapReduce | Spark |
|:---|:---|:---|
| 처리 방식 | 디스크 기반 | **인메모리** |
| 속도 | 느림 | **최대 100배 빠름** |
| 지원 언어 | Java | Python, Scala, Java, R |
| 반복 처리 | 매번 디스크 I/O | 메모리 캐싱으로 빠름 |
| 실시간 처리 | ❌ | ✅ (Spark Streaming) |

---

## 핵심 개념

### RDD (Resilient Distributed Dataset)
- Spark의 기본 데이터 단위
- 여러 노드에 분산 저장된 데이터 컬렉션
- 불변(Immutable), 장애 시 자동 복구

### DataFrame / Dataset
- RDD 위에 스키마(컬럼 구조)를 얹은 것
- SQL처럼 쓸 수 있어 더 직관적
- 현재 가장 많이 사용하는 방식

### Lazy Evaluation
- 변환(Transformation)은 즉시 실행하지 않고 Action이 호출될 때 한꺼번에 실행
- 불필요한 연산을 줄여 최적화

```python
# Transformation (실행 안 됨)
df = df.filter(df.age > 20).select("name", "age")

# Action (이때 실제 실행)
df.show()
```

---

## 아키텍처

```
[Driver Program]      ← 사용자 코드 실행, 전체 조율
     ↓
[Cluster Manager]     ← 리소스 배분 (YARN / Kubernetes / Standalone)
     ↓
[Executor] × N        ← 실제 데이터 처리 (각 Worker 노드에서 실행)
```

---

## 구성 요소

| 모듈 | 역할 |
|:---|:---|
| **Spark Core** | 기본 분산 처리 엔진 |
| **Spark SQL** | SQL 및 DataFrame API |
| **Spark Streaming** | 실시간 스트림 처리 |
| **MLlib** | 머신러닝 라이브러리 |
| **GraphX** | 그래프 처리 |

---

## 주요 사용 사례

- 대용량 로그 분석
- 데이터 변환 (ETL)
- 머신러닝 학습 (MLlib)
- 실시간 스트림 처리
- SQL on Hadoop (Spark SQL)
