# Databricks 아키텍처 개념 정리

---

## Control Plane vs Data Plane

### 개념

Databricks는 두 개의 영역으로 나뉘어 동작.

```
[Control Plane]                    [Data Plane]
Databricks가 관리                   고객사가 관리 (Customer Managed VPC)
  │                                   │
  ├─ Workspace UI                     ├─ 클러스터 EC2 (실제 연산)
  ├─ Job 스케줄러                      ├─ S3 (데이터 저장)
  ├─ Notebook 관리                     └─ VPC / Subnet / SG
  ├─ 클러스터 생성/삭제 명령
  └─ Unity Catalog 메타데이터
```

### Control Plane

Databricks가 운영하는 **중앙 관리 서버**.
사용자가 Notebook을 실행하거나 Job을 등록하면 Control Plane이 명령을 처리.

```
역할:
  - Workspace UI 제공 (브라우저로 접속하는 화면)
  - 클러스터 생성 / 삭제 명령 전송
  - Job 스케줄링 및 실행 관리
  - Unity Catalog 메타데이터 저장
  - 사용자 인증 / 권한 관리

위치:
  - Databricks의 AWS 계정에 존재
  - 고객사가 직접 접근하거나 수정 불가
```

### Data Plane

실제 **데이터 처리가 일어나는 곳**. 고객사 VPC 안에 존재.

```
역할:
  - 클러스터 EC2 (Driver + Worker 노드)
  - 실제 Spark 연산 수행
  - S3 데이터 읽기/쓰기
  - 고객 데이터가 실제로 있는 공간

위치:
  - 고객사 AWS 계정 / VPC 안 (Customer Managed VPC)
  - 또는 Databricks 관리 VPC (Databricks Managed)
```

### 통신 구조

```
사용자 브라우저
  │
  ▼
Control Plane (Databricks 계정)
  │  클러스터 생성 명령 / Job 실행 지시
  │  포트 6666 (Inbound), 8443~8451 (Outbound)
  ▼
Data Plane (고객사 VPC - EC2 클러스터)
  │  실제 데이터 처리
  ▼
S3 (데이터 저장)
```

### 고객 데이터가 Control Plane을 거치지 않는 이유

```
Notebook 코드      → Control Plane 경유 (명령만)
실제 데이터 처리   → Data Plane 내부에서만 동작
S3 데이터          → Data Plane ↔ S3 직접 통신

→ 고객 데이터는 고객사 VPC 밖으로 나가지 않음
→ Control Plane에는 메타데이터와 명령만 전달
```

---

## STS (Security Token Service)

> 상세 내용 → [02_aws-scp-ram.md](./02_aws-scp-ram.md)

**임시 자격증명 발급 서비스.** Cross Account Role에서 `sts:AssumeRole`로 사용.

```
Databricks Control Plane
  │
  └─ sts:AssumeRole → 임시 자격증명 발급 (최대 12시간)
                           │
                           └─ 고객사 S3 / EC2 접근
```

---

## Kinesis

### 개념

**실시간 스트리밍 데이터를 수집/처리하는 AWS 서비스.**
데이터가 발생하는 즉시 수집 → 처리 → 저장하는 파이프라인.

```
S3      = 창고 (데이터 쌓아두고 나중에 꺼냄)
Kinesis = 컨베이어 벨트 (데이터가 실시간으로 계속 흘러옴)
```

### Kinesis 종류

| 서비스 | 용도 |
|--------|------|
| **Kinesis Data Streams** | 실시간 데이터 스트림 수집/처리 |
| **Kinesis Data Firehose** | 스트림 데이터를 S3/Redshift 등에 자동 저장 |
| **Kinesis Data Analytics** | 스트림 데이터를 SQL로 실시간 분석 |

### S3 vs Kinesis 비교

```
S3 (배치):
  데이터 쌓임 → 일정 주기마다 처리
  예) 하루치 로그 모아서 새벽에 분석

Kinesis (스트리밍):
  데이터 발생 즉시 처리
  예) 카드 결제 즉시 이상 거래 탐지
      IoT 센서 데이터 실시간 모니터링
```

### Databricks + Kinesis 연동

```
[데이터 소스]
  IoT 센서 / 앱 로그 / 결제 시스템
  │
  ▼
Kinesis Data Streams (실시간 수집)
  │
  ▼
Databricks Structured Streaming (Data Plane에서 실시간 처리)
  │
  ▼
Delta Table → S3 저장
```

**Databricks에서 Kinesis 읽기 예시:**
```python
df = (spark.readStream
  .format("kinesis")
  .option("streamName", "dosan-prod-stream")
  .option("region", "ap-northeast-2")
  .option("initialPosition", "latest")
  .load()
)
```

### POC에서 Kinesis가 필요한 경우

```
배치 처리만 필요: S3 + Databricks 충분
실시간 처리 필요: Kinesis → Databricks Structured Streaming
```

---

## 전체 아키텍처 흐름 (POC 기준)

```
[두산/테스나 시스템]
  데이터 생성
  │
  ├─ 배치: S3 업로드
  │         └─ External Location → Volume → Databricks 처리
  │
  └─ 실시간: Kinesis 전송
              └─ Databricks Structured Streaming → Delta Table

[Databricks]
  Control Plane (Databricks 계정)
    │ 명령 전송 (포트 6666, 8443~8451)
    ▼
  Data Plane (고객사 VPC)
    │ EC2 클러스터 (Driver + Worker)
    │ Spark 연산
    ▼
  S3 (결과 저장)
    └─ Unity Catalog Volume으로 접근
```
