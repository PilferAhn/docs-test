# MapReduce — 배치 분산 처리 프레임워크

> Hadoop의 구성요소 | Google의 MapReduce 논문(2004) 기반으로 구현

---

## 한 줄 정의

**대용량 데이터를 Map(분류)과 Reduce(집계) 두 단계로 나눠 병렬 처리하는 프레임워크**

---

## 핵심 개념

### Map 단계
- 입력 데이터를 쪼개서 각 노드가 독립적으로 처리
- 결과를 Key-Value 쌍으로 출력

### Shuffle & Sort
- Map 결과를 Key 기준으로 정렬하고 같은 Key끼리 묶음
- 자동으로 처리됨

### Reduce 단계
- 같은 Key로 묶인 Value들을 집계
- 최종 결과 출력

---

## 동작 흐름

```
[Input Data]
     ↓ 분할
[Map Task × N]     ex) 단어 세기: "hello" → (hello, 1)
     ↓ Shuffle & Sort
[Reduce Task × M]  ex) (hello, [1,1,1]) → (hello, 3)
     ↓
[Output Data]
```

---

## 예시 — 단어 세기 (Word Count)

```
입력:  "hello world hello"

Map:
  hello → 1
  world → 1
  hello → 1

Shuffle & Sort:
  hello → [1, 1]
  world → [1]

Reduce:
  hello → 2
  world → 1

출력:  hello 2 / world 1
```

---

## 특징

| 항목 | 내용 |
|:---|:---|
| 처리 방식 | 디스크 기반 (각 단계마다 HDFS에 쓰고 읽음) |
| 장애 내성 | Task 실패 시 자동 재실행 |
| 확장성 | 노드 추가만으로 처리량 선형 증가 |
| 단점 | 디스크 I/O 많아 Spark 대비 느림 |

---

## Spark과 비교

| 항목 | MapReduce | Spark |
|:---|:---|:---|
| 중간 결과 저장 | 디스크 (HDFS) | 메모리 |
| 반복 알고리즘 | 매번 디스크 I/O | 메모리 캐싱 |
| 속도 | 기준점 | 최대 100배 빠름 |
| 실시간 처리 | ❌ | ✅ |
| 현재 사용 | 줄어드는 추세 | 주류 |

> MapReduce는 Spark 이전의 표준이었으나, 현재는 대부분 Spark으로 대체됨.
> 개념 이해 측면에서 여전히 중요.
