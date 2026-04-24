# Impala (Gemini 답변)

> 출처: Gemini 답변 원문
> Gemini는 Impala를 CDW(Cloudera Data Warehouse) 카테고리 안에서 Hive와 함께 다뤘습니다.

## CDW (Cloudera Data Warehouse) — Impala 포함

### Cloudera CDW 설명
Apache Hive(LLAP)와 **Impala** 엔진을 사용합니다.
- 클라우드에서 'Virtual Warehouse'를 생성해 독립적인 쿼리 성능을 보장
- 대규모 동시 접속 처리에 최적화

### Impala의 위치
CDW에서 Impala는 **빠른 대화형 SQL**을 담당합니다.
Hive가 복잡한 ETL 배치에 강하다면, Impala는 저지연 조회에 특화됩니다.

### Databricks 대응: Databricks SQL (DB SQL)
- **Photon 엔진**: C++ 기반의 고성능 SQL 실행 엔진으로 Impala 수준의 성능 제공
- 서버리스 SQL 웨어하우스로 관리 부담 최소화
- Tableau, Power BI 등 BI 도구와의 연결성 우수

### 주요 차이점
| 항목 | Impala (CDW) | Databricks SQL |
|:---|:---|:---|
| 실행 엔진 | MPP 분산 엔진 | Photon (C++ 기반 Spark) |
| 배포 방식 | Virtual Warehouse | SQL Warehouse (Serverless 지원) |
| 강점 | HDFS 기반 저지연 SQL | 속도, 서버리스, 클라우드 네이티브 |
