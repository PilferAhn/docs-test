# Apache Hadoop — 분산 저장 및 처리 플랫폼

> Apache Software Foundation 오픈소스 프로젝트 | 최초 릴리즈: 2006년 (Yahoo! / Doug Cutting 개발)

---

## 한 줄 정의

**수백~수천 대의 일반 서버를 묶어 대용량 데이터를 저장하고 처리하는 플랫폼**

---

## 핵심 구성 요소

```
Hadoop
├── HDFS        (분산 파일 시스템)
├── YARN        (리소스 관리)
├── MapReduce   (배치 분산 처리)
└── Common      (공통 유틸리티)
```

---

## HDFS (Hadoop Distributed File System)

- 파일을 **블록(기본 128MB)** 단위로 쪼개서 여러 노드에 분산 저장
- 각 블록을 **3벌 복제** (기본값) → 노드 장애 시 자동 복구
- 한 번 쓰고 여러 번 읽는 패턴에 최적화

```
파일 (1GB)
├── Block 1 (128MB) → DataNode 1, 2, 3 에 복제
├── Block 2 (128MB) → DataNode 2, 3, 4 에 복제
├── Block 3 (128MB) → DataNode 1, 3, 5 에 복제
...
```

### 역할별 노드

| 노드 | 역할 |
|:---|:---|
| **NameNode** | 파일 메타데이터 관리 (어느 블록이 어디 있는지) |
| **DataNode** | 실제 데이터 블록 저장 |
| **Secondary NameNode** | NameNode 메타데이터 백업 |

---

## YARN (Yet Another Resource Negotiator)

- 클러스터 전체의 CPU / 메모리 자원을 관리하고 배분
- Hadoop 2.x부터 도입 — MapReduce 외 다른 처리 엔진(Spark 등)도 실행 가능

| 컴포넌트 | 역할 |
|:---|:---|
| **ResourceManager** | 클러스터 전체 자원 관리 |
| **NodeManager** | 각 노드의 자원 관리 |
| **ApplicationMaster** | 개별 Job의 실행 조율 |

---

## 아키텍처 (전체)

```
[Client]
   ↓ 파일 업로드
[NameNode]  ←→  [DataNode × N]   (HDFS)

[ResourceManager]  ←→  [NodeManager × N]  (YARN)
        ↓
   [MapReduce / Spark / ...]
```

---

## 주요 사용 사례

- 대용량 로그/이벤트 데이터 저장소
- 데이터 레이크(Data Lake) 기반
- 배치 ETL 파이프라인
- Hive / Impala / Spark의 스토리지 레이어
