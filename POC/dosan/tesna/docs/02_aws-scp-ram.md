# AWS SCP, RAM & Cross Account Role

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

---

## Cross Account Role

### 개념

**다른 AWS 계정의 리소스에 접근**하기 위해 IAM Role을 위임(AssumeRole)하는 방식.
계정 간 직접 자격증명 공유 없이 안전하게 권한 위임 가능.

```
계정 A (Databricks)           계정 B (고객사 - 두산/테스나)
  │                                    │
  │  sts:AssumeRole ──────────────▶  IAM Role (Cross Account Role)
  │                                    │
  │◀─────────── 임시 자격증명 발급 ─────┘
  │
  └─ 고객사 S3, EC2 등 리소스 접근
```

### 동작 원리

1. 고객사 계정(B)에서 Cross Account Role 생성
2. Role의 Trust Policy에 Databricks 계정(A) ID 등록
3. Databricks가 `sts:AssumeRole`로 임시 자격증명 획득
4. 임시 자격증명으로 고객사 리소스 접근 (유효시간: 최대 12시간)

### 설정 방법

#### 1. 고객사 계정(B)에서 Role 생성

**Trust Policy (누가 이 Role을 쓸 수 있는가):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::DATABRICKS_ACCOUNT_ID:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "DATABRICKS_EXTERNAL_ID"
        }
      }
    }
  ]
}
```

**Permission Policy (이 Role로 뭘 할 수 있는가):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket",
        "ec2:DescribeInstances"
      ],
      "Resource": "*"
    }
  ]
}
```

#### 2. Databricks 계정(A)에서 AssumeRole 권한 부여

```json
{
  "Effect": "Allow",
  "Action": "sts:AssumeRole",
  "Resource": "arn:aws:iam::고객사_ACCOUNT_ID:role/cross-account-role명"
}
```

### SCP와의 관계

```
고객사 계정에 SCP가 있으면 Cross Account Role 권한도 제한됨

SCP: s3:PutObject 금지
  └─ Cross Account Role에 s3:PutObject 있어도 → 접근 불가
```

### Databricks에서 사용되는 Cross Account Role 종류

| Role | 용도 | 누가 AssumeRole |
|------|------|----------------|
| **Root Role** | Metastore UC Bucket(S3) 접근 | Databricks UC 서비스 |
| **Storage Credential Role** | External Location S3 접근 | Databricks UC 서비스 |
| **Instance Profile Role** | 클러스터 EC2가 직접 S3 접근 | EC2 인스턴스 |
| **Workspace Role** | Customer Managed VPC 배포용 | Databricks Control Plane |

---

## UC Role이 Cross Account Role인 이유

### 핵심 구조

Databricks는 **자체 AWS 계정**에서 운영되고, 고객 데이터는 **고객사 AWS 계정**의 S3에 있다.
두 계정이 다르기 때문에 Databricks → 고객사 S3 접근은 반드시 Cross Account 방식이어야 한다.

```
[Databricks AWS 계정]              [고객사 AWS 계정 (두산/테스나)]
  │                                         │
  │  Unity Catalog 서비스                   │  S3 버킷 (UC Bucket / External)
  │                                         │  IAM Role (UC Role = Root Role)
  │                                         │
  └─ sts:AssumeRole ──────────────────────▶ UC Role
                                             │
  ◀──────── 임시 자격증명 발급 ──────────────┘
  │
  └─ S3 접근 (Read/Write)
```

**즉, UC Role은 Cross Account Role의 한 종류이며, S3 접근에 특화된 버전이다.**

---

### UC Role의 두 가지 종류

#### 1. Root Role (Metastore용)

Databricks Unity Catalog 서비스가 **Metastore 루트 스토리지(UC Bucket)** 에 접근할 때 사용.

```
역할: Databricks UC 서비스 → 고객사 UC Bucket(S3)
생성 위치: 고객사 AWS 계정
지정 위치: Databricks Metastore 생성 시 1회 등록
```

**Trust Policy - 누가 이 Role을 쓸 수 있나:**
```json
{
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::DATABRICKS_ACCOUNT_ID:root"
  },
  "Action": "sts:AssumeRole",
  "Condition": {
    "StringEquals": {
      "sts:ExternalId": "DATABRICKS_EXTERNAL_ID"
    }
  }
}
```

**Permission Policy - 이 Role로 뭘 할 수 있나:**
```json
{
  "Effect": "Allow",
  "Action": [
    "s3:GetObject",
    "s3:PutObject",
    "s3:DeleteObject",
    "s3:ListBucket",
    "s3:GetBucketLocation",
    "s3:ListBucketMultipartUploads",
    "s3:AbortMultipartUpload",
    "s3:ListMultipartUploadParts"
  ],
  "Resource": [
    "arn:aws:s3:::uc-root-버킷명",
    "arn:aws:s3:::uc-root-버킷명/*"
  ]
}
```

#### 2. Storage Credential Role (External Location용)

Databricks UC가 **고객사 원본 데이터 버킷(External Bucket)** 에 접근할 때 사용.
Root Role과 구조는 동일하나, 접근 대상 S3 버킷이 다름.

```
역할: Databricks UC 서비스 → 고객사 External Bucket(S3)
생성 위치: 고객사 AWS 계정
지정 위치: Databricks > Unity Catalog > Storage Credentials에 등록
```

Root Role과 **분리해서 만드는 것을 권장** (최소 권한 원칙).

---

### Root Role vs Storage Credential Role 비교

| | Root Role | Storage Credential Role |
|--|-----------|------------------------|
| **대상 버킷** | UC Bucket (Metastore 루트) | External Bucket (고객 원본 데이터) |
| **등록 위치** | Metastore 생성 시 | Storage Credential 생성 시 |
| **개수** | Metastore당 1개 | External Location 수만큼 |
| **데이터 성격** | Managed Table 저장소 | 고객사 원본 데이터 |

---

### 전체 흐름 정리

```
고객사 AWS 계정
  ├─ S3: uc-root-bucket        ← Metastore 루트
  │    └─ Bucket Policy: Databricks Account 허용
  │
  ├─ S3: dosan-raw-bucket      ← 고객사 원본 데이터
  │    └─ Bucket Policy: Databricks Account 허용
  │
  ├─ IAM Role: Root Role       ← UC Bucket 접근용 Cross Account Role
  │    ├─ Trust: Databricks Account ID + External ID
  │    └─ Permission: uc-root-bucket Read/Write
  │
  └─ IAM Role: Storage Credential Role  ← External Bucket 접근용 Cross Account Role
       ├─ Trust: Databricks Account ID + External ID
       └─ Permission: dosan-raw-bucket Read/Write

Databricks 계정
  └─ Unity Catalog
       ├─ Metastore → AssumeRole(Root Role) → uc-root-bucket
       └─ External Location → AssumeRole(Storage Credential Role) → dosan-raw-bucket
```

### POC 체크리스트

- [ ] 고객사 AWS Account ID 확보
- [ ] Databricks AWS Account ID 확보 (Databricks 콘솔에서 확인)
- [ ] Databricks External ID 확보 (Databricks 콘솔에서 확인)
- [ ] Root Role 생성 (고객사 계정) + Trust Policy 설정
- [ ] Storage Credential Role 생성 (고객사 계정) + Trust Policy 설정
- [ ] UC Bucket에 Bucket Policy 추가 (Databricks Account 허용)
- [ ] External Bucket에 Bucket Policy 추가 (Databricks Account 허용)
- [ ] SCP로 인한 차단 여부 확인
