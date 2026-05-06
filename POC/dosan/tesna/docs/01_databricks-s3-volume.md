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

## Bucket Policy

### 개념

S3 버킷 자체에 붙이는 **리소스 기반 접근 제어 정책**.
IAM Policy가 "사람 기준"이라면, Bucket Policy는 "버킷 기준"으로 누가 접근할 수 있는지 정의.

### IAM Policy vs Bucket Policy 차이

| | IAM Policy | Bucket Policy |
|--|-----------|---------------|
| **붙는 위치** | IAM User / Role | S3 버킷 |
| **제어 방향** | 이 사람이 뭘 할 수 있나 | 이 버킷에 누가 접근할 수 있나 |
| **계정 범위** | 같은 계정 중심 | 다른 계정도 허용 가능 |
| **Principal** | 없음 (주체가 곧 이 Policy 보유자) | 명시 필요 (누구를 허용할지) |

### 구조

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::DATABRICKS_ACCOUNT_ID:role/역할명"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::버킷명",
        "arn:aws:s3:::버킷명/*"
      ]
    }
  ]
}
```

- `Principal` = 누가 (IAM Policy에는 없는 항목, Bucket Policy의 핵심)
- `Action` = 뭘 할 수 있나
- `Resource` = 어느 버킷/경로에

### Databricks에서 Bucket Policy가 필요한 경우

```
상황 1: Cross Account 접근
  고객사 계정 S3 ← Databricks 계정(다른 계정)에서 접근
  → Bucket Policy에 Databricks Role ARN을 Principal로 추가

상황 2: IAM Role만으로 부족할 때
  IAM Role에 권한 있어도 Bucket Policy가 Deny면 접근 불가
  → 양쪽 다 Allow여야 최종 접근 가능

상황 3: 특정 VPC에서만 접근 허용
  → Bucket Policy에 VPC Endpoint 조건 추가
```

### 권한 최종 판단 로직

```
S3 접근 가능 여부 =
  SCP (Allow)
  AND Bucket Policy (Allow 또는 미설정)
  AND IAM Policy (Allow)

→ 셋 중 하나라도 Deny면 접근 불가
```

### VPC Endpoint 조건 추가 예시 (특정 VPC에서만 허용)

```json
{
  "Effect": "Deny",
  "Principal": "*",
  "Action": "s3:*",
  "Resource": [
    "arn:aws:s3:::버킷명",
    "arn:aws:s3:::버킷명/*"
  ],
  "Condition": {
    "StringNotEquals": {
      "aws:SourceVpce": "vpce-0a1b2c3d4e5f"
    }
  }
}
```

→ 지정한 VPC Endpoint를 통하지 않은 접근은 전부 Deny.

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
