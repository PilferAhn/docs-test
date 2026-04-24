# CDW - Cloudera Data Warehouse (Claude 정리)

> GPT 답변 + Gemini 답변을 종합 정리한 버전

## CDW란?

**정형 데이터를 SQL로 조회하고 BI 리포팅을 수행하는 클라우드 데이터 웨어하우스 서비스**입니다.

## Cloudera에서의 역할

Gemini 관점 (CDW 전체):
- Apache Hive(LLAP)와 Impala 엔진을 사용
- 클라우드에서 Virtual Warehouse를 생성해 독립적 성능 보장
- 대규모 동시 접속 처리에 최적화

GPT 관점 (개별 컴포넌트):
- Impala: 저지연 MPP SQL (빠른 대화형 쿼리)
- Hive on Tez/LLAP: 복잡한 SQL 및 ETL
- Hive Metastore: 테이블 스키마 정보 저장

## Databricks 대응

두 LLM 모두 **Databricks SQL**을 핵심 대응으로 지목합니다.

| CDW 구성 요소 | Databricks 대응 |
|:---|:---|
| Impala (빠른 SQL) | **SQL Warehouse (Photon 엔진)** |
| Hive LLAP (배치 SQL) | **Databricks Compute (Spark)** |
| Hive Metastore | **Unity Catalog metastore** |
| Virtual Warehouse | **SQL Warehouse** |
| Serverless 옵션 | **Serverless SQL Warehouse** |
| BI 도구 연결 | **Partner Connect** (Tableau, Power BI 등) |

### 기술적 비교

| 항목 | Cloudera CDW | Databricks SQL |
|:---|:---|:---|
| 실행 엔진 | Hive LLAP / Impala MPP | Photon (C++ 벡터화 엔진) |
| 메타스토어 | Hive Metastore (별도) | Unity Catalog (통합) |
| 권한 관리 | Ranger (별도) | Unity Catalog (내장) |
| 서버리스 | 지원 | 더 고도화 |
| 강점 | 전통 SQL 호환성, 대규모 동시 접속 | 속도, 서버리스, BI 연결성 |

## 한 줄 요약

**CDW ≈ Databricks SQL (SQL Warehouse + Unity Catalog)**
