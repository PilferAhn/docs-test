# Databricks - S3 연동 및 Volume 설정

## 개요

S3 버킷에 데이터를 올려두면 Databricks에서 Volume으로 자동 접근 가능.
고객사(또는 담당자)가 S3에 파일을 업로드하면 Databricks에서 바로 조회 가능한 구조.

---

## 연동 방식

```
S3 버킷
  └─ Unity Catalog External Location 등록
       └─ Databricks Volume으로 노출
            └─ dbfs:/Volumes/catalog/schema/volume_name/ 경로로 접근
```

### 전제 조건

- IAM Role에 S3 접근 권한 부여
- Databricks Unity Catalog 활성화
- External Location 등록 (Databricks Admin 계정으로)

---

## IAM Role 최소 권한

```json
{
  "Version": "2012-10-17",
  "Statement": [
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
        "arn:aws:s3:::버킷명",
        "arn:aws:s3:::버킷명/*"
      ]
    }
  ]
}
```

### Trust Relationship (필수)

Databricks의 AWS Account ID를 AssumeRole로 허용해야 함.

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

---

## 설정 절차 요약

1. AWS에서 S3 버킷 생성
2. IAM Role 생성 + S3 권한 정책 연결
3. Trust Relationship에 Databricks Account 추가
4. Databricks > Unity Catalog > External Locations에 등록
5. Volume 생성 후 경로 확인

---

## 참고

- External Location은 Databricks Admin 권한 필요
- 고객사가 S3에 파일 업로드만 하면 나머지는 자동
- IAM Role 권한은 최소 권한 원칙 적용 권장
