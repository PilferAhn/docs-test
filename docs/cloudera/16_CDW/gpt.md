# CDW - Cloudera Data Warehouse (GPT 답변)

> 출처: ChatGPT 답변 원문
> GPT는 CDW를 직접 다루지 않고, CDW 내 개별 컴포넌트(Hive, Impala 등)를 중심으로 설명했습니다.

## GPT가 다룬 관련 컴포넌트

CDW는 다음 하둡 컴포넌트들을 CDP 상위 서비스로 묶은 것입니다.

### Impala → Databricks SQL Warehouse
- Impala: 저지연 MPP SQL 엔진
- 대응: **Databricks SQL Warehouse** (가장 직접적인 1:1 대응)
- 상세 내용: `04_Impala/gpt.md` 참고

### Hive on Tez → SQL Warehouse + Spark Compute
- Hive on Tez: SQL 쿼리 엔진 (배치/ETL 중심)
- 대응: 용도에 따라 **SQL Warehouse** 또는 **Spark Compute**
- 상세 내용: `03_Hive-on-Tez/gpt.md` 참고

### Hive Metastore → Unity Catalog
- HMS: 테이블 메타데이터 저장소
- 대응: **Unity Catalog metastore**
- 상세 내용: `02_Hive-Metastore/gpt.md` 참고

## GPT 관점 요약

CDW를 구성하는 핵심 컴포넌트들의 대응 관계:
- **Impala(빠른 SQL)** → **Databricks SQL Warehouse**
- **Hive(ETL SQL)** → **Databricks Compute(Spark)**
- **Hive Metastore** → **Unity Catalog**
