# POC 기술 정리 문서

두산-테스나 POC 진행 중 정리한 AWS / Databricks 기술 개념 문서 모음.

---

## 목차

| # | 파일 | 내용 |
|---|------|------|
| 01 | [databricks-s3-volume.md](./01_databricks-s3-volume.md) | S3 → Databricks Volume 연동, IAM Role 권한 |
| 02 | [aws-scp-ram.md](./02_aws-scp-ram.md) | SCP(서비스 제어 정책), RAM(리소스 공유) |
| 03 | [aws-networking.md](./03_aws-networking.md) | VPC, Gateway, Security Group, NACL, 포트 설정 |
| 04 | [terraform.md](./04_terraform.md) | Terraform 개념 및 POC 활용 |
| 05 | [deploy-prefix.md](./05_deploy-prefix.md) | 리소스 네이밍 및 Prefix 전략 |
| 06 | [databricks-vpc-setup.md](./06_databricks-vpc-setup.md) | Databricks Managed vs Customer Managed VPC |

---

## 핵심 결정 사항

- **Prefix**: `dosan`
- **네이밍 규칙**: `dosan-{env}-{resource-type}`
- **VPC 방식**: 고객사 보안 정책 확인 후 결정 필요
- **S3 연동**: External Location + Unity Catalog Volume 방식
