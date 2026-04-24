# Hive Metastore (Claude 정리)

> GPT 답변 + Gemini 답변을 종합 정리한 버전

## Hive Metastore란?

**테이블의 설계도(메타데이터)를 저장하는 서비스**입니다.

도서관의 **도서 목록 카드**에 비유할 수 있습니다.
- 실제 책(데이터) → HDFS/S3 같은 저장소에 있음
- 어떤 책이 어느 위치에 있고, 어떤 분류인지 → HMS(도서 목록 카드)가 보관

## Cloudera에서의 역할

HMS는 Hive만 쓰는 것이 아닙니다. **Impala, Spark 등 여러 서비스가 공유**합니다.

저장하는 정보:
- 데이터베이스 이름, 테이블 이름, 컬럼 이름과 타입
- 데이터가 어느 HDFS 경로에 있는지
- 파티션(날짜·지역 등으로 나눈 단위) 정보
- SerDe(데이터 직렬화 방식) 정보

백엔드는 MySQL, PostgreSQL 같은 일반 RDBMS를 사용합니다.

## Databricks 대응

GPT는 **Unity Catalog metastore**를 직접 대응으로 지목합니다.
Gemini도 Unity Catalog가 메타데이터 역할을 담당한다고 설명합니다.

단, 두 답변 모두 **Unity Catalog는 HMS보다 훨씬 더 넓은 개념**임을 강조합니다.

| 항목 | Hive Metastore | Unity Catalog |
|:---|:---|:---|
| 테이블 메타데이터 | ✅ | ✅ |
| 접근 권한 관리 | ❌ (Ranger가 담당) | ✅ 내장 |
| 데이터 계보(Lineage) | ❌ (Atlas가 담당) | ✅ 내장 |
| AI 모델·함수 관리 | ❌ | ✅ |
| 클라우드 간 공유 | ❌ | ✅ (Delta Sharing) |
| 네임스페이스 | database.table | catalog.schema.table (3단계) |

## 한 줄 요약

**Hive Metastore ≈ Unity Catalog의 메타스토어 기능**
(Unity Catalog는 메타데이터 + 권한 + 계보 + AI자산까지 포함하는 상위 개념)
