# AWS 네트워킹 개념 정리

---

## 기본 구조

```
인터넷
  │
  ▼ (Inbound)
[Internet Gateway]
  │
  ▼
[Public Subnet]
  - NAT Gateway
  - Bastion Host (필요 시)
  │
  ▼ (Outbound only)
[Private Subnet]
  - Databricks 클러스터
  - RDS, 내부 서비스
  │
  ▼
[Transit Gateway] ─── 다른 VPC / 온프레미스
```

---

## 주요 개념

### Internet Gateway

- VPC와 인터넷을 연결하는 관문
- Public Subnet에서 인터넷 접근 가능하게 해줌

### NAT Gateway

- Private Subnet → 인터넷 Outbound 연결 담당
- 인터넷에서 Private Subnet으로는 직접 접근 불가 (단방향)
- Databricks 클러스터가 패키지 다운로드 등 외부 통신 시 필요

### Transit Gateway

- 여러 VPC를 중앙에서 연결하는 허브
- VPC Peering은 1:1 연결이지만 Transit Gateway는 N:N 연결 가능
- 멀티 계정, 멀티 VPC 환경에서 사용

### Inbound / Outbound

**초등학생도 이해하는 설명:**

```
내 집(서버)을 기준으로 생각하면 된다.

Inbound = 누군가 우리 집 문을 두드리는 것 (들어오는 것)
  예) 택배기사가 집으로 택배를 가져옴
  예) 친구가 우리 집에 방문
  → 외부 → 내부 방향

Outbound = 내가 밖으로 나가는 것 (나가는 것)
  예) 내가 편의점에 사러 나감
  예) 내가 친구 집에 전화함
  → 내부 → 외부 방향
```

네트워크에서:

```
Inbound  = 인터넷(외부) → 내 서버(내부)로 들어오는 트래픽
           예) 사용자가 웹사이트 접속, Databricks Control Plane이 클러스터에 명령 전송

Outbound = 내 서버(내부) → 인터넷(외부)으로 나가는 트래픽
           예) 클러스터가 패키지 다운로드, S3에 데이터 저장
```

| 구분 | 방향 | 비유 | 예시 |
|------|------|------|------|
| Inbound | 외부 → 내부 | 택배가 집으로 옴 | 사용자가 서비스 접속 |
| Outbound | 내부 → 외부 | 내가 밖에 나감 | 클러스터가 패키지 다운로드 |

---

## Subnet

### 정의

VPC(가상 네트워크)를 더 작게 나눈 **네트워크 구역**.
IP 대역을 분리해서 역할별로 구분하고, 각 구역에 다른 보안 정책 적용 가능.

```
VPC (10.0.0.0/16) - 전체 네트워크 공간
  ├─ Public Subnet  (10.0.1.0/24) ← 인터넷과 직접 통신 가능
  └─ Private Subnet (10.0.2.0/24) ← 인터넷 직접 접근 불가, 내부 전용
```

### Public vs Private Subnet

| | Public Subnet | Private Subnet |
|--|--------------|----------------|
| **인터넷 접근** | 직접 가능 | 불가 (NAT Gateway 경유) |
| **주요 용도** | NAT Gateway, Load Balancer | 클러스터, DB, 내부 서비스 |
| **라우팅** | Internet Gateway로 연결 | NAT Gateway로 Outbound만 |

### Subnet CIDR과 IP 개수

CIDR 표기법으로 IP 범위를 정의. 숫자가 클수록 IP 개수가 적음.

| CIDR | IP 개수 | 실제 사용 가능 | 용도 |
|------|---------|--------------|------|
| /16 | 65,536 | ~65,531 | VPC 전체 |
| /24 | 256 | ~251 | 일반 Subnet |
| /26 | 64 | ~59 | 소규모 Subnet |

### Private Subnet을 쓴다는 의미

Databricks 클러스터(EC2)를 **인터넷에서 직접 접근할 수 없는 구역**에 배포한다는 뜻.

```
[Public Subnet]
인터넷 ──────────────────▶ EC2 (직접 접근 가능, 공인 IP 있음)

[Private Subnet]
인터넷 ──────── 차단 ────── EC2 (직접 접근 불가, 사설 IP만 존재)
```

**Outbound(나가는 것)는 NAT Gateway를 통해 가능:**

```
Private Subnet EC2
  │
  │ Outbound (패키지 다운로드, API 호출 등)
  ▼
NAT Gateway (Public Subnet에 위치)
  │
  ▼
인터넷

반대 방향 (Inbound):
인터넷 → Private Subnet EC2  ← 직접 접근 불가
```

**왜 Private Subnet을 쓰는가:**
- 클러스터 EC2에 외부에서 직접 SSH, 포트 스캔 등 불가
- 공인 IP가 없으므로 인터넷에 노출되지 않음
- 클러스터가 처리하는 데이터가 내부 네트워크에만 존재

**그럼 Control Plane은 어떻게 클러스터에 접근하나:**

```
방법 1: NAT Gateway 경유 (일반 방식)
  Control Plane → 인터넷 → NAT Gateway → 클러스터

방법 2: Back-end Private Link (보안 강화)
  Control Plane → AWS PrivateLink → 클러스터 (인터넷 없음)
```

Security Group에서 Databricks Control Plane IP만 허용해 다른 외부 접근은 차단.

---

### Databricks에서 Subnet이 중요한 이유

**1. 클러스터 배포 위치**
Databricks 클러스터(EC2)는 반드시 **Private Subnet**에 배포됨.
외부에서 직접 접근 불가 → 보안 강화.

**2. IP 개수 = 클러스터 스케일 한계**
```
Subnet /24 → 최대 약 250개 IP → EC2 250대
Subnet /26 → 최대 약 60개 IP  → EC2 60대

클러스터 노드가 많이 필요하면 → 넉넉한 CIDR 필요
```

**3. Multi-AZ 필수 (Subnet 최소 2개)**
Databricks는 서로 다른 가용영역(AZ)의 Subnet을 2개 이상 요구.
```
ap-northeast-2a → Private Subnet A (10.0.2.0/24)
ap-northeast-2c → Private Subnet B (10.0.3.0/24)
```

**4. VPC Endpoint 연결 대상**
S3 VPC Endpoint를 Databricks 클러스터가 있는 Subnet에 연결해야
S3 트래픽이 인터넷을 거치지 않고 내부로 통신 가능.

**5. Security Group / NACL 적용 단위**
Subnet이 정해져야 어떤 SG/NACL을 적용할지 결정 가능.

---

## Security Group

### 정의

EC2 인스턴스(ENI) 레벨의 **가상 방화벽**.
인바운드/아웃바운드 트래픽을 포트/IP 기준으로 허용 제어.

```
특징:
- Stateful: 인바운드 허용 시 응답(Outbound) 자동 허용
- Allow만 가능 (Deny 규칙 없음)
- 여러 인스턴스에 동일 SG 적용 가능
- 인스턴스에 여러 SG 동시 부착 가능
```

### 규칙 예시

```
Inbound Rules:
  Type     Protocol  Port   Source
  HTTPS    TCP       443    0.0.0.0/0          ← 외부 접근 허용
  MySQL    TCP       3306   10.0.0.0/16        ← VPC 내부만 허용
  Custom   TCP       3006   sg-0a1b2c3d        ← 특정 SG끼리만 허용

Outbound Rules:
  Type     Protocol  Port   Destination
  All      All       All    0.0.0.0/0          ← 모든 외부 접근 허용
```

---

## Security Group vs NACL

| 항목 | Security Group | NACL |
|------|---------------|------|
| 적용 단위 | EC2 인스턴스 (ENI) | 서브넷 |
| 상태 | Stateful (응답 자동 허용) | Stateless (인/아웃 둘 다 명시 필요) |
| 규칙 방식 | 허용만 가능 | 허용/거부 모두 가능 |
| 우선순위 | 모든 규칙 평가 후 허용 | 번호 순서대로 평가 |

### 포트 3006 체크

- Security Group과 NACL 양쪽에서 3006 포트 허용 필요
- NACL은 Stateless이므로 **인바운드 + 아웃바운드 둘 다** 명시 필요
- Security Group은 Stateful이므로 인바운드 허용 시 응답은 자동 허용

```
예시 - NACL 설정 (Stateless)
  Inbound:  3006 허용 (외부 → 내부)
  Outbound: 3006 허용 (내부 → 외부) ← 빠뜨리기 쉬운 부분
```

---

## VPC Endpoint

### 정의

인터넷을 거치지 않고 AWS 서비스(S3, DynamoDB 등)에 **VPC 내부에서 직접 접근**하는 전용 통로.

```
[일반 방식 - 인터넷 경유]
EC2 (Private Subnet) → NAT Gateway → 인터넷 → S3

[VPC Endpoint 방식 - 내부 직접 연결]
EC2 (Private Subnet) → VPC Endpoint → S3  (인터넷 없음)
```

### 종류

| 종류 | 방식 | 주요 대상 서비스 |
|------|------|----------------|
| **Gateway Endpoint** | 라우팅 테이블에 경로 추가 | S3, DynamoDB |
| **Interface Endpoint** | Subnet에 ENI(네트워크 인터페이스) 생성 | 대부분의 AWS 서비스 |

### 식별자

| 항목 | 형식 | 의미 |
|------|------|------|
| **VPC ID** | `vpc-0a1b2c3d4e5f` | VPC 자체 식별자 |
| **VPC Endpoint ID** | `vpce-0a1b2c3d4e5f` | VPC Endpoint 식별자 |

```
VPC (vpc-0a1b2c3d4e5f)
  ├─ Subnet
  ├─ Security Group
  └─ VPC Endpoint (vpce-0a1b2c3d4e5f) ← S3 내부 통신 통로
```

### Databricks에서 S3 VPC Endpoint가 필요한 이유

- Databricks 클러스터는 Private Subnet에 있어 인터넷 직접 접근 불가
- S3 VPC Endpoint 없으면 S3 접근 시 NAT Gateway → 인터넷 경유 → 비용 + 보안 위험
- S3 VPC Endpoint 설정 시 내부 직접 통신 → 비용 절감 + 보안 강화

```
설정 위치:
  VPC > Endpoints > Create Endpoint
    Service: com.amazonaws.ap-northeast-2.s3 (Gateway 타입)
    VPC: 해당 VPC 선택
    Route Table: Private Subnet 라우팅 테이블 선택
```

---

## Private Link

### 정의

AWS PrivateLink = 인터넷을 거치지 않고 서비스에 **VPC 내부에서 직접 접근**하는 전용 통로.
Databricks에서는 두 구간에 각각 적용.

```
[사용자 브라우저 / API 클라이언트]
          │
          │ ← Front-end Private Link
          ▼
[Databricks Control Plane]
          │
          │ ← Back-end Private Link
          ▼
[고객사 VPC - 클러스터 EC2 (Data Plane)]
```

### Front-end Private Link

**사용자 → Databricks Workspace** 구간을 인터넷 없이 연결.

```
[일반 방식]
사용자 → 인터넷 → Databricks Workspace (공인 IP)

[Front-end Private Link]
사용자 → 고객사 VPC → Interface Endpoint → Databricks Workspace
```

- 언제 필요: 보안 정책상 인터넷 경유 불가, Workspace를 공인 IP로 노출하고 싶지 않을 때

### Back-end Private Link

**Databricks Control Plane → 고객사 클러스터(EC2)** 구간을 인터넷 없이 연결.

```
[일반 방식]
Control Plane → 인터넷 → NAT Gateway → 클러스터 EC2

[Back-end Private Link]
Control Plane → AWS PrivateLink → 클러스터 EC2
```

- 언제 필요: 클러스터 제어 트래픽의 인터넷 경유를 차단하고 싶을 때

### Front-end vs Back-end 비교

| | Front-end | Back-end |
|--|-----------|----------|
| **구간** | 사용자 ↔ Workspace | Control Plane ↔ 클러스터 |
| **차단 대상** | 외부 인터넷에서 UI/API 접근 | 클러스터 제어 통신의 인터넷 경유 |
| **구현 방식** | Interface VPC Endpoint | Interface VPC Endpoint |

### AWS 구현

```
VPC > Endpoints > Create Endpoint
  Type: Interface
  Service: com.amazonaws.vpce.ap-northeast-2.databricks-XXXXX
  Subnet: Databricks 클러스터 Subnet 선택
  Security Group: Databricks 전용 SG 선택
```

---

## Route 53 / DNS / Firewall (Private Link 완성을 위한 추가 설정)

### 왜 필요한가

Private Link(VPC Endpoint)를 만들어도 **DNS가 공인 IP를 가리키면 트래픽이 Private Link를 타지 않음**.
DNS 설정으로 트래픽을 Private Link 통로로 유도해야 완성됨.

```
[Private Link만 만든 상태 - 문제]
사용자가 workspace.cloud.databricks.com 접속
  → DNS 조회 → 공인 IP 반환 → 인터넷으로 접속 (Private Link 미사용)

[Route 53 설정 후 - 정상]
사용자가 workspace.cloud.databricks.com 접속
  → DNS 조회 → Route 53 Private Hosted Zone → VPC Endpoint 사설 IP 반환
  → Private Link 경유 접속
```

### Route 53 Private Hosted Zone

VPC 내부에서만 동작하는 **사설 DNS 서버**.

```
생성:
  도메인: cloud.databricks.com
  연결 VPC: 고객사 VPC

효과:
  VPC 내부에서 workspace URL 조회 시
  → Private Hosted Zone이 응답
  → VPC Endpoint 사설 IP 반환 (공인 IP 대신)
```

### DNS Record (A Record)

Private Hosted Zone 안에 Workspace URL → VPC Endpoint IP를 매핑하는 레코드.

```
A Record:
  이름:  *.cloud.databricks.com
  값:    10.0.1.45 (VPC Endpoint의 사설 IP)

→ VPC 내부 DNS 조회 시 사설 IP 반환
→ 트래픽이 Private Link를 타게 됨
```

### Route 53 Inbound Resolver Endpoint

온프레미스나 다른 VPC에서 이 Private Hosted Zone의 DNS를 조회할 수 있는 진입점.

```
온프레미스 사용자
  │
  └─ VPN / Direct Connect
        │
        └─ Route 53 Inbound Resolver Endpoint (고객사 VPC 내 생성)
              │
              └─ Private Hosted Zone 조회 → VPC Endpoint IP 반환
```

- 온프레미스 연결이 없으면 불필요
- VPC 내부 사용자만 있을 경우 Private Hosted Zone만으로 충분

### Firewall

DNS + Private Link 설정 후 **인터넷 직접 접근을 차단**하는 마지막 관문.

```
허용:
  VPC Endpoint → Databricks (내부 통신)
  특정 포트 / IP만 허용

차단:
  Databricks 도메인으로의 직접 인터넷 트래픽
  Public Access OFF 시 완전 차단
```

### 전체 설정 순서

```
1. VPC Endpoint (Interface) 생성
      └─ Databricks PrivateLink 서비스 연결

2. Route 53 Private Hosted Zone 생성
      └─ 고객사 VPC에 연결

3. DNS A Record 등록
      └─ workspace URL → VPC Endpoint 사설 IP

4. Route 53 Inbound Resolver 생성 (온프레미스 연결 시)
      └─ 외부에서 Private Hosted Zone 조회 가능하게

5. Firewall 규칙 설정
      └─ 인터넷 직접 접근 차단
      └─ Private Link 경로만 허용
```

> Private Link = 통로 생성
> Route 53 + Record = 트래픽을 그 통로로 유도
> Firewall = 인터넷 우회 차단

---

## 0.0.0.0/0 의미

### 개념

**"모든 IP 주소"** 를 뜻하는 표기법.

```
특정 IP 하나:   10.0.1.5/32    → 이 IP 딱 하나만
특정 대역:      10.0.0.0/16    → 10.0.x.x 대역 전체
모든 IP:        0.0.0.0/0      → 지구상의 모든 IP 전부
```

### 초등학생 비유

```
집 문 앞에 경비원이 있다고 생각하면:

특정 IP   = "홍길동만 들어와"
대역 지정 = "우리 회사 직원들만 들어와"
0.0.0.0/0 = "아무나 다 들어와"
```

### 실제 규칙에서 의미

```
Inbound  443  TCP  0.0.0.0/0  ALLOW
→ 전 세계 어디서든 443 포트로 접근 허용
→ 웹사이트 공개 접근 시 사용

Outbound  443  TCP  0.0.0.0/0  ALLOW
→ 어디로든 443 포트로 나가는 것 허용
→ 클러스터가 어떤 외부 서버든 HTTPS 통신 가능
```

### Databricks에서 사용 기준

```
0.0.0.0/0 써도 되는 경우:
  Outbound 443  → 클러스터가 어디든 HTTPS 통신 필요

0.0.0.0/0 쓰면 안 되는 경우:
  Inbound 6666  → Control Plane IP만 허용해야 함
                   0.0.0.0/0이면 전 세계 누구나 접근 가능 → 위험
  Inbound 3306  → DB는 절대 전체 오픈 금지
```

### 주의사항

```
가능하면 특정 IP 또는 대역으로 제한할 것.
0.0.0.0/0은 공개 서비스(80, 443)의 Inbound 또는
외부 통신이 필요한 Outbound에만 제한적으로 사용.
```

---

## Databricks 필수 포트 (6666, 8443~8451)

### 왜 이 포트들이 필요한가

Databricks는 **Secure Cluster Connectivity (SCC)** 구조를 사용.
클러스터가 Control Plane에 **먼저 터널을 연결**하고, Control Plane이 그 터널을 통해 클러스터를 제어.

```
[클러스터 EC2 - Private Subnet]
  │
  │ Outbound 8443~8451 (클러스터가 먼저 터널 연결)
  ▼
[Databricks Control Plane]
  │
  │ Inbound 6666 (터널을 통해 클러스터에 명령 전송)
  ▼
[클러스터 EC2]
```

### 각 포트 역할

| 포트 | 방향 | 용도 |
|------|------|------|
| **443** | Outbound | HTTPS - 기본 통신 |
| **6666** | Inbound | SCC 터널 수신 - Control Plane 명령 받는 포트 |
| **8443~8451** | Outbound | SCC 터널 연결 - 클러스터가 Control Plane에 터널 개설 |

### 포트가 빠졌을 때 발생하는 문제

```
8443~8451 Outbound 없음
  → 클러스터가 Control Plane에 터널 연결 불가
  → 클러스터 상태가 Pending에서 멈춤
  → Notebook 연결 안 됨, Job 실행 안 됨

6666 Inbound 없음
  → Control Plane이 클러스터에 명령 전송 불가
  → 클러스터는 켜졌는데 아무것도 실행 안 됨
```

### Security Group 설정 (필수 포트 전체)

```
Inbound Rules:
  Port 6666        TCP   Databricks Control Plane IP   ← SCC 터널 수신

Outbound Rules:
  Port 443         TCP   0.0.0.0/0                     ← HTTPS
  Port 8443~8451   TCP   Databricks Control Plane IP   ← SCC 터널 연결
```

### NACL 설정 주의 (Stateless - 양방향 모두 명시)

```
Inbound:
  Rule 100  Port 6666       TCP   Databricks Control Plane IP   ALLOW
  Rule 110  Port 8443-8451  TCP   Databricks Control Plane IP   ALLOW  ← 응답 트래픽

Outbound:
  Rule 100  Port 443        TCP   0.0.0.0/0                     ALLOW
  Rule 110  Port 8443-8451  TCP   Databricks Control Plane IP   ALLOW
  Rule 120  Port 6666       TCP   Databricks Control Plane IP   ALLOW  ← 응답 트래픽
```

> NACL은 Stateless → 인바운드 허용해도 아웃바운드 응답을 따로 허용해야 함.
> Security Group은 Stateful → 인바운드 허용 시 응답은 자동 허용.

---

## POC 체크포인트

- [ ] Private Subnet 최소 2개 (Multi-AZ)
- [ ] NAT Gateway 구성 (Outbound 인터넷 필요 시)
- [ ] S3 VPC Endpoint (Gateway) 구성
- [ ] Databricks Private Link (Interface Endpoint) 구성
- [ ] Route 53 Private Hosted Zone + A Record 설정
- [ ] Route 53 Inbound Resolver (온프레미스 연결 시)
- [ ] Security Group: Databricks 전용 SG 생성
- [ ] NACL: 인/아웃바운드 포트 규칙 양방향 확인
- [ ] Firewall: 인터넷 직접 접근 차단 규칙
- [ ] Databricks Control Plane IP 대역 화이트리스트 추가
