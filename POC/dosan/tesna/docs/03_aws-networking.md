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

| 구분 | 방향 | 예시 |
|------|------|------|
| Inbound | 외부 → 내부 | 사용자가 서비스 접속 |
| Outbound | 내부 → 외부 | 클러스터가 패키지 다운로드 |

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

## POC 체크포인트

- [ ] Private Subnet 최소 2개 (Multi-AZ)
- [ ] NAT Gateway 구성 (Outbound 인터넷 필요 시)
- [ ] S3 VPC Endpoint 구성 (S3 트래픽을 인터넷 안 거치게)
- [ ] Security Group: Databricks 전용 SG 생성
- [ ] NACL: 인/아웃바운드 포트 규칙 양방향 확인
- [ ] Databricks Control Plane IP 대역 화이트리스트 추가
