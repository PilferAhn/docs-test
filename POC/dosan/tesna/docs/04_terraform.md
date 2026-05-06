# Terraform 개요

---

## 개념

- **IaC (Infrastructure as Code)**: 인프라를 코드로 정의하고 관리
- AWS, Azure, GCP 등 클라우드 리소스를 코드 파일로 선언
- `terraform apply` 한 번으로 전체 인프라 자동 생성/변경/삭제

---

## 왜 쓰는가

| 수동 설정 | Terraform |
|-----------|-----------|
| 콘솔에서 클릭 클릭 | 코드 한 번 작성 후 반복 실행 |
| 설정 히스토리 없음 | Git으로 버전 관리 |
| 환경마다 다시 설정 | dev/stg/prod 동일 코드 재사용 |
| 실수 발생 가능 | 코드 리뷰로 사전 검토 가능 |

---

## 기본 동작 원리

```
.tf 파일 작성 (리소스 선언)
  │
  ▼
terraform plan   → 변경사항 미리 확인 (dry-run)
  │
  ▼
terraform apply  → 실제 리소스 생성/변경
  │
  ▼
terraform destroy → 리소스 삭제
```

---

## 예시 - S3 버킷 생성

```hcl
resource "aws_s3_bucket" "dosan_raw" {
  bucket = "dosan-prod-raw-data"

  tags = {
    Project     = "dosan"
    Environment = "prod"
  }
}
```

---

## POC 관련 활용 포인트

- VPC, 서브넷, NAT Gateway, Security Group 등 네트워크 일괄 생성
- IAM Role, Policy 코드화 → 실수 방지
- Databricks workspace 생성도 Terraform Provider로 가능
- 환경(dev/prod) 분리 시 변수(variable)만 바꿔서 재사용

---

## 참고

- Terraform Registry에서 Databricks Provider 공식 지원
- `databricks/databricks` 프로바이더로 workspace, cluster, job 등 코드로 관리 가능
