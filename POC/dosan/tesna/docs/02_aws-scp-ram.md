# AWS SCP & RAM

---

## SCP (Service Control Policy)

### 개념

- AWS Organizations에서 사용하는 **조직 단위 최상위 권한 정책**
- 멤버 계정 전체 또는 특정 OU(Organizational Unit)에 적용
- IAM 권한이 있어도 SCP가 막으면 사용 불가

### 권한 우선순위

```
SCP (조직 레벨)
  └─ IAM Policy (계정 레벨)
       └─ Resource Policy (리소스 레벨)
```

SCP에서 허용된 범위 안에서만 IAM이 동작함.

### 주요 사용 사례

- 특정 리전 외 리소스 생성 금지
- S3 퍼블릭 버킷 생성 금지
- 특정 서비스 사용 금지 (예: 특정 계정에서 EC2 생성 제한)

### POC 관련 체크포인트

- 고객사 AWS 계정에 SCP가 걸려 있으면 IAM Role 권한이 있어도 S3/EC2 등 접근 불가
- 고객사 클라우드 담당자에게 SCP 정책 확인 필요

---

## RAM (Resource Access Manager)

### 개념

- AWS 계정 간 리소스 공유 서비스
- 별도 계정 생성 없이 리소스를 다른 계정에서 사용 가능하게 함

### 공유 가능한 주요 리소스

| 리소스 | 사용 사례 |
|--------|-----------|
| Transit Gateway | 멀티 계정 VPC 연결 |
| Subnet | 공유 VPC 구성 |
| Route53 Resolver Rule | DNS 공유 |
| License Manager | 소프트웨어 라이선스 공유 |

### POC 관련 체크포인트

- 두산/테스나 계정과 Databricks 계정 간 네트워크 리소스 공유 시 RAM 사용 가능
- Transit Gateway를 RAM으로 공유하면 각 계정의 VPC를 중앙에서 연결 가능
