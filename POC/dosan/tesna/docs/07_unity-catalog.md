# Unity Catalog (UC) 개념 정리

---

## Unity Catalog란

Databricks의 **중앙 데이터 거버넌스 시스템**.
테이블, 파일, 모델 등 데이터 자산을 한 곳에서 관리하고 권한 제어.

```
Unity Catalog 계층 구조:
  Metastore (리전당 1개)
    └─ Catalog
         └─ Schema (Database)
              ├─ Table (Managed / External)
              └─ Volume (파일 스토리지)
```

---

## UC Bucket (루트 스토리지)

### 개념

Unity Catalog Metastore가 데이터를 저장하는 **전용 S3 버킷**.

```
UC Bucket = s3://dosan-prod-uc-root/
  └─ Managed Table 실제 파일
  └─ UC 내부 메타데이터
  └─ Metastore 기본 저장 위치
```

### 버킷 종류 비교

| 버킷 | 용도 | 관리 주체 |
|------|------|-----------|
| **UC Bucket** | Metastore 루트 스토리지 | Databricks (UC가 라이프사이클 관리) |
| **External Bucket** | 고객 원본 데이터 | 고객사 (직접 관리) |

- **Managed Table** → UC Bucket에 저장 (테이블 삭제 시 데이터도 삭제됨)
- **External Table** → External Bucket에 저장 (테이블 삭제해도 데이터 유지)

---

## Root Role (루트 IAM Role)

### 개념

Databricks가 UC Bucket(S3)에 접근할 때 사용하는 **IAM Role**.
**Cross Account Role의 한 종류**로, 고객사 AWS 계정에 생성하고 Databricks 계정이 AssumeRole해서 사용한다.

> 상세 내용 → [02_aws-scp-ram.md - UC Role이 Cross Account Role인 이유](./02_aws-scp-ram.md)

```
[Databricks AWS 계정]          [고객사 AWS 계정]
  Unity Catalog 서비스
  │
  └─ sts:AssumeRole ────────▶ Root Role (고객사 계정에 존재)
                                   │
  ◀─── 임시 자격증명 발급 ──────────┘
  │
  └─ S3 Read/Write ─────────▶ UC Bucket (고객사 S3)
```

### 필요한 권한

```json
{
  "Action": [
    "s3:GetObject",
    "s3:PutObject",
    "s3:DeleteObject",
    "s3:ListBucket",
    "s3:GetBucketLocation"
  ],
  "Resource": [
    "arn:aws:s3:::uc-root-버킷명",
    "arn:aws:s3:::uc-root-버킷명/*"
  ]
}
```

### Trust Relationship

```json
{
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

## UC Root vs Root Role 비교

| | UC Root | Root Role |
|--|---------|-----------|
| **정체** | S3 경로 (버킷) | IAM Role |
| **역할** | Metastore 데이터 저장 위치 | 그 S3에 접근하기 위한 권한 주체 |
| **비유** | 창고 주소 | 창고 열쇠 |

```
관계:
  Root Role ─────────────▶ UC Root (S3)
  (접근 권한을 가진 IAM)     (데이터가 저장되는 위치)
```

> UC Root에 **접근하려면** Root Role이 필요하고,
> Root Role이 **가리키는 곳**이 UC Root.

---

## Metastore 생성 시 설정 항목

```
Databricks Account Console > Metastore 생성
  ├─ 이름: dosan-prod-metastore
  ├─ 리전: ap-northeast-2
  ├─ Root Storage (UC Root):  s3://dosan-prod-uc-root/
  └─ IAM Role (Root Role):    arn:aws:iam::계정ID:role/dosan-prod-uc-root-role
```

- 둘 중 하나라도 빠지면 Metastore 생성 불가
- Metastore는 **리전당 1개** 생성 권장

---

## External Location (고객 데이터 연결)

UC Bucket과 별도로 고객사 S3 버킷을 UC에 연결하는 방식.

```
고객사 S3 (원본 데이터)
  └─ External Location 등록 (Databricks Admin)
       └─ Volume으로 노출
            └─ dbfs:/Volumes/catalog/schema/volume_name/
```

External Location에도 별도 IAM Role 필요 (Root Role과 분리 권장).

---

## SCC + REST만 주면 된다

### 의미

AWS 사전 설정(Cross Account Role, Bucket Policy)이 완료된 상태라면,
Databricks에서 External Location 연결 시 **두 가지만** 입력하면 끝.

| 항목 | 내용 |
|------|------|
| **SCC** (Storage Credential Configuration) | IAM Role ARN을 Databricks에 등록한 자격증명 객체 |
| **REST** (S3 URL) | 연결할 S3 버킷 경로 (`s3://버킷명/경로/`) |

### SCC란

Databricks가 Cross Account Role(IAM Role)을 사용하기 위한 **래퍼(wrapper) 객체**.
IAM Role ARN을 Databricks Storage Credential로 등록하면 UC가 해당 Role로 S3에 접근 가능해짐.

```
Storage Credential =
  IAM Role ARN을 Databricks에 "이 Role로 S3 접근해" 라고 등록한 것
```

### 전체 흐름

```
사전 작업 (AWS - 복잡한 부분)
  ├─ Cross Account Role 생성 (고객사 계정)
  ├─ Trust Policy 설정 (Databricks Account ID + External ID)
  └─ S3 Bucket Policy 설정

        ↓ 완료 후

Databricks 설정 (간단한 부분)
  ① Storage Credential 등록
       이름: dosan-storage-cred
       IAM Role ARN: arn:aws:iam::고객사계정ID:role/storage-cred-role
                                                        ← SCC

  ② External Location 생성
       Storage Credential: dosan-storage-cred (위에서 만든 것)
       URL: s3://dosan-prod-raw-bucket/data/
                                                        ← REST (S3 URL)

        ↓ 완료

  Volume으로 자동 노출
  → dbfs:/Volumes/catalog/schema/volume_name/
```

### 핵심 포인트

- AWS 설정(Role, Policy)이 복잡한 것이지, **Databricks 쪽 설정 자체는 SCC + URL로 단순**
- SCC는 재사용 가능 → 같은 Role로 여러 External Location 생성 시 SCC 하나로 공유
- Storage Credential은 **Databricks Admin만** 생성/수정 가능

---

## POC 설정 순서

```
1. UC Root용 S3 버킷 생성
2. Root Role (IAM Role) 생성 + S3 권한 연결
3. Trust Relationship 설정 (Databricks Account ID)
4. Databricks Metastore 생성 (UC Root + Root Role 지정)
5. 고객사 데이터용 External Bucket 연결 (External Location)
6. Volume 생성 후 접근 테스트
```
