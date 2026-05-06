# Deploy Prefix 전략

---

## 개념

- 배포 시 생성되는 AWS 리소스명 앞에 붙는 식별자
- 환경, 프로젝트, 리전 등을 구분하기 위해 사용
- 리소스명 충돌 방지 + 한눈에 어떤 리소스인지 파악 가능

---

## 두산-테스나 POC 기준

### Prefix 규칙

```
{project}-{env}-{resource-type}

예시:
dosan-prod-databricks-workspace
dosan-prod-s3-raw
dosan-dev-iam-role-databricks
dosan-prod-sg-cluster
```

### 확정된 Prefix

- **프로젝트명**: `dosan`
- **환경**: `dev` / `stg` / `prod`
- **리소스 타입**: 해당 리소스 약어 사용

---

## 리소스별 네이밍 예시

| 리소스 | 네이밍 예시 |
|--------|------------|
| S3 버킷 (raw) | `dosan-prod-s3-raw` |
| S3 버킷 (processed) | `dosan-prod-s3-processed` |
| Databricks Workspace | `dosan-prod-dbx-workspace` |
| IAM Role | `dosan-prod-iam-role-dbx` |
| Security Group | `dosan-prod-sg-dbx-cluster` |
| VPC | `dosan-prod-vpc` |
| Subnet (private) | `dosan-prod-subnet-private-1a` |
| Transit Gateway | `dosan-prod-tgw` |

---

## 고유성 확보 방법

S3 버킷은 전 세계 고유해야 하므로 추가 suffix 필요:

```
옵션 1: AWS Account ID 일부 사용
  dosan-prod-s3-raw-123456

옵션 2: 리전 코드 포함
  dosan-prod-s3-raw-apne2

옵션 3: 랜덤 suffix
  dosan-prod-s3-raw-a3f9
```

---

## Terraform에서 Prefix 관리

```hcl
variable "prefix" {
  default = "dosan"
}

variable "env" {
  default = "prod"
}

locals {
  name_prefix = "${var.prefix}-${var.env}"
}

resource "aws_s3_bucket" "raw" {
  bucket = "${local.name_prefix}-s3-raw"
}
```

환경 변경 시 `env` 변수만 바꾸면 전체 리소스명 자동 변경.
