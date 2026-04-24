# Hive on Tez (Gemini 답변)

> 출처: Gemini 답변 원문
> Gemini는 Hive on Tez를 CDW(Cloudera Data Warehouse) 카테고리 안에서 다뤘습니다.

## CDW (Cloudera Data Warehouse) — Hive on Tez 포함

### Cloudera CDW 설명
Apache Hive(LLAP)와 Impala 엔진을 사용합니다.
- 클라우드에서 'Virtual Warehouse'를 생성해 독립적인 쿼리 성능을 보장
- 대규모 동시 접속 처리에 최적화

Hive LLAP(Live Long And Process)는 Hive on Tez의 발전형으로, 메모리에 데이터를 캐싱해 응답 속도를 높인 버전입니다.

### Databricks 대응: Databricks SQL (DB SQL)
- 최근 Databricks가 가장 주력하는 서비스
- **Photon 엔진**: C++ 기반의 고성능 SQL 실행 엔진
- 서버리스 SQL 웨어하우스를 통해 관리 부담을 최소화
- Tableau, Power BI 같은 툴과의 연결성이 매우 뛰어남

### 주요 차이점
| 항목 | Cloudera CDW (Hive) | Databricks SQL |
|:---|:---|:---|
| 실행 엔진 | Hive LLAP / Tez | Photon (C++ 기반) |
| 운영 방식 | Virtual Warehouse | SQL Warehouse (Serverless 지원) |
| 강점 | 전통적 SQL 호환성 | 속도, 서버리스, BI 연결성 |
