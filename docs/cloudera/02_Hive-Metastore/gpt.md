# Hive Metastore (GPT 답변)

> 출처: ChatGPT 답변 원문

## Cloudera에서의 역할

Hive Metastore(HMS)는 **테이블 메타데이터 저장소**입니다. Hive뿐 아니라 **Impala, Spark 등 여러 서비스가 공유**하며, 백엔드 RDBMS(MySQL/PostgreSQL 등)에 메타데이터를 저장합니다.

쉽게 말해 "실제 데이터는 HDFS/S3 등에 있고, 그 데이터의 스키마/위치/파티션/속성 정보는 HMS에 있다"는 구조입니다.

### 저장하는 정보
- 데이터베이스, 테이블, 컬럼, 파티션, SerDe, 위치(path) 등의 정의
- Hive가 SQL을 해석할 때 참조
- Impala도 같은 메타스토어를 공유해 같은 테이블을 볼 수 있음
- Spark도 HMS를 참조해 테이블을 읽는 구성이 흔함

## Databricks 대응

가장 직접적인 대응은 **Unity Catalog metastore**입니다.

Unity Catalog는 데이터/AI 자산 거버넌스를 통합 제공하고, catalog-schema-table의 3단계 네임스페이스를 사용합니다.

### 중요한 차이
- **Hive Metastore**: 주로 "테이블 메타데이터 저장소"
- **Unity Catalog**: "메타데이터 + 권한 + 계보 + 외부 스토리지 거버넌스 + 비정형 파일/모델/함수까지 포함한 통합 거버넌스 계층"

## 한 줄 매핑

**Hive Metastore ≈ Unity Catalog metastore**
단, Unity Catalog가 더 상위 개념입니다.
