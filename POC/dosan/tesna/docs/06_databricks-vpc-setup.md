# Databricks VPC / EC2 설정

---

## 핵심 질문

> VPC랑 EC2가 내 꺼가 아니면 설정해야 될 게 많아?

**결론: 많아집니다.** 아래 두 가지 케이스로 구분됩니다.

---

## Case 1: Databricks Managed VPC (기본값)

Databricks가 자체 AWS 계정에 VPC/EC2를 직접 생성하고 관리.

### 설정 난이도: 낮음

```
필요한 설정:
1. Databricks workspace 생성
2. S3 접근용 IAM Role 설정
   └─ 끝
```

### 장점

- 네트워크 설정 불필요
- 빠른 시작 가능

### 단점

- 고객사 네트워크와 격리됨
- 온프레미스 연결 어려움
- 보안 정책이 엄격한 고객사에는 부적합

---

## Case 2: Customer Managed VPC

고객사 AWS 계정의 VPC 안에 Databricks 클러스터를 배포.

### 설정 난이도: 높음

### 필요한 IAM 권한

```json
EC2 관련:
- ec2:RunInstances
- ec2:TerminateInstances
- ec2:DescribeInstances
- ec2:CreateSecurityGroup
- ec2:AuthorizeSecurityGroupIngress / Egress

VPC 관련:
- ec2:DescribeVpcs
- ec2:DescribeSubnets
- ec2:DescribeRouteTables

S3 관련:
- s3:GetObject / PutObject / ListBucket 등

STS 관련:
- sts:AssumeRole

추가 (상황에 따라):
- kms:* (암호화 사용 시)
- cloudformation:* (스택 배포 시)
- iam:PassRole
```

### 추가로 설정해야 할 인프라

| 항목 | 설명 |
|------|------|
| Private Subnet x2 | Multi-AZ 구성 (최소 2개) |
| NAT Gateway | 클러스터 Outbound 인터넷 연결 |
| S3 VPC Endpoint | S3 트래픽을 인터넷 없이 직접 연결 |
| Security Group | Databricks 전용 SG (Control Plane IP 허용) |
| Databricks IP 화이트리스트 | Control Plane 통신용 IP 허용 |

### Databricks Control Plane 통신 구조

```
Databricks Control Plane (Databricks 관리)
  │
  │ HTTPS (443), WebSocket
  ▼
NAT Gateway
  │
  ▼
클러스터 (고객사 Private Subnet의 EC2)
```

---

## 케이스 비교 요약

| 항목 | Databricks Managed | Customer Managed VPC |
|------|-------------------|----------------------|
| VPC 소유 | Databricks | 고객사 |
| EC2 소유 | Databricks | 고객사 |
| 설정 복잡도 | 낮음 | 높음 |
| 보안 제어 | 제한적 | 완전 제어 |
| 온프레미스 연결 | 어려움 | 가능 |
| 고객사 네트워크 접근 | 불가 | 가능 |

---

## POC 권장 방향

- **빠른 POC 검증**: Case 1 (Databricks Managed) 사용
- **실제 운영 환경 연동 필요**: Case 2 (Customer Managed VPC)
- 두산/테스나 보안 정책 확인 후 케이스 결정 필요

---

## Public Access 설정

### 개념

Databricks Workspace에 **인터넷(공인 IP)으로 접근을 허용할지** 결정하는 설정.

```
Public Access = ON (기본값)
  → 인터넷에서 workspace URL 직접 접근 가능
  → Private Link와 동시에 사용 가능 (둘 다 허용)

Public Access = OFF
  → 인터넷 접근 완전 차단
  → Private Link 경로로만 접근 가능
```

### Public Access ON + Private Link 병행 (POC 권장)

```
내부 사용자 → Private Link 경유 접속
외부 사용자 → 인터넷 경유 접속 (둘 다 허용)
```

**왜 POC에서 ON으로 두는가:**
- Private Link만 쓰면 고객사 VPC 내부에서만 접근 가능
- 외부 개발자, Databricks 지원팀 등 접근 불가
- VPN 없으면 아무도 못 들어옴 → POC 진행 어려움

### Public Access OFF (운영 권장)

```
인터넷 → Workspace 접근 완전 차단
Private Link → 접근 가능

필요 선행 조건:
  - Private Link 설정 완료
  - Route 53 Private Hosted Zone + DNS Record 설정 완료
  - 사용자가 VPN 또는 내부 네트워크에 연결된 상태
```

### 단계별 전환 전략

```
POC 단계
  Public Access = ON
  Private Link 설정 (내부 통신용)
  → 외부/내부 모두 접근 가능, 빠른 개발/검증

운영 전환 시
  Public Access = OFF
  Private Link 필수
  Route 53 + DNS 설정 완료 후
  → 보안 강화, 인터넷 노출 완전 차단
```

---

## 누락하기 쉬운 설정

### 1. VPC DNS 설정

VPC 자체에 DNS 옵션 2개가 반드시 활성화되어 있어야 함.

```
VPC 설정 > Edit DNS:
  ✅ enableDnsHostnames = true
  ✅ enableDnsSupport   = true

꺼져 있으면:
  → Route 53 Private Hosted Zone 설정해도 DNS 동작 안 함
  → VPC Endpoint IP 대신 공인 IP로 연결됨
```

### 2. NACL Ephemeral Port

NACL은 Stateless → 응답 트래픽용 임시 포트도 열어야 함.

```
추가해야 할 규칙:
  Inbound   1024-65535  TCP  0.0.0.0/0  ALLOW
  Outbound  1024-65535  TCP  0.0.0.0/0  ALLOW
```

### 3. Security Group Self Outbound

Self 규칙을 Inbound만 추가하고 Outbound를 빠뜨리는 경우.

```
Inbound  Self ← 보통 추가함
Outbound Self ← 빠뜨리기 쉬움 → Spark Shuffle 안 됨
```

### 4. Metastore → Workspace 할당

Metastore 만들고 Workspace에 연결하는 것 빠뜨리는 경우.

```
Databricks Account Console
  > Metastore 선택
  > Workspaces 탭
  > Assign to Workspace ← 이거 빠뜨리면 UC 기능 전혀 안 됨
```

### 5. Workspace에 네트워크 설정 입력

Customer Managed VPC 사용 시 Workspace 생성할 때 직접 입력해야 함.

```
Workspace 생성 시 입력 항목:
  - VPC ID
  - Private Subnet ID (2개)
  - Security Group ID
  - VPC Endpoint ID (Private Link 사용 시)

빠지면 → Databricks Managed VPC로 생성됨
```

### 6. Storage Credential → External Location → Volume 순서

```
필수 순서:
  1. Storage Credential 등록 (IAM Role ARN)
  2. External Location 생성 (SCC + S3 URL)
  3. Volume 생성
  4. 접근 테스트

2번 없이 3번 → Volume 생성 불가
```

---

## 체크리스트 (Customer Managed VPC 선택 시)

**네트워크:**
- [ ] VPC enableDnsHostnames = true
- [ ] VPC enableDnsSupport = true
- [ ] 고객사 AWS 계정 ID 확보
- [ ] VPC ID, Subnet ID (Private x2) 확인
- [ ] NAT Gateway 존재 여부 확인
- [ ] S3 VPC Endpoint (Gateway) 생성
- [ ] Databricks Private Link (Interface Endpoint) 생성
- [ ] Route 53 Private Hosted Zone + DNS A Record 설정
- [ ] Security Group 생성 (Self Inbound/Outbound, 포트 6666, 8443-8451)
- [ ] NACL Ephemeral Port (1024-65535) 인/아웃바운드 추가
- [ ] Public Access 설정 (POC: ON, 운영: OFF)
- [ ] SCP 정책 차단 여부 확인

**IAM / S3:**
- [ ] Cross-Account IAM Role 생성 + Trust Policy
- [ ] UC Bucket Bucket Policy (Databricks Account Principal)
- [ ] External Bucket Bucket Policy
- [ ] STS AssumeRole 권한 확인

**Databricks:**
- [ ] Workspace에 VPC ID / Subnet ID / SG ID 입력
- [ ] Metastore 생성 (UC Root + Root Role)
- [ ] Metastore → Workspace 할당
- [ ] Storage Credential 등록
- [ ] External Location 생성
- [ ] Volume 생성 및 접근 테스트
