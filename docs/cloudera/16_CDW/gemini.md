# CDW - Cloudera Data Warehouse (Gemini 답변)

> 출처: Gemini 답변 원문

## 2. 데이터 웨어하우징 (SQL Analytics)

정형 데이터를 쿼리하고 BI 리포팅을 수행하는 단계입니다.

### Cloudera Data Warehouse (CDW)
Apache Hive(LLAP)와 Impala 엔진을 사용합니다.
- 클라우드에서 **'Virtual Warehouse'**를 생성해 독립적인 쿼리 성능을 보장
- 대규모 동시 접속 처리에 최적화

### Databricks 대응: Databricks SQL (DB SQL)
최근 Databricks가 가장 주력하는 서비스입니다.
- **Photon 엔진**: C++ 기반의 고성능 SQL 실행 엔진으로 매우 빠름
- **서버리스 SQL 웨어하우스**: 서버 관리 없이 SQL 쿼리 실행 가능
- Tableau, Power BI 같은 BI 도구와의 연결성이 매우 뛰어남

### 주요 차이점
| 항목 | Cloudera CDW | Databricks SQL |
|:---|:---|:---|
| 실행 엔진 | Hive LLAP / Impala | Photon (C++ 기반 Spark) |
| 배포 방식 | Virtual Warehouse | SQL Warehouse (Serverless 지원) |
| BI 연결 | JDBC/ODBC 중심 | Partner Connect (Tableau, Power BI 등) |
| 강점 | 전통적 SQL 호환성, 대규모 동시 접속 | 속도, 서버리스, BI 연결성 |
