# Cloudera vs Databricks 전체 매핑 (Claude 정리)

> GPT 답변 + Gemini 답변을 종합 정리한 버전

## 두 플랫폼은 왜 1:1 대응이 안 되나?

GPT와 Gemini 모두 동일한 핵심을 지적합니다.

- **Cloudera**: 개별 부품(서비스)을 사용자가 직접 보고 조합하는 구조
- **Databricks**: 여러 기능이 하나의 통합 플랫폼 안으로 합쳐진 구조

GPT는 하둡 컴포넌트 수준(HDFS, YARN, Hive 등)에서 상세 비교했고,
Gemini는 CDP 상위 서비스 수준(CDE, CDW, CML, CDF, SDX)에서 카테고리 비교했습니다.
두 관점을 합치면 아래와 같은 완전한 그림이 됩니다.

## 전체 매핑 (GPT + Gemini 통합)

| Cloudera 서비스/컴포넌트 | 관점 | Databricks 대응 | 대응 정밀도 |
|:---|:---|:---|:---|
| HDFS | 하둡 컴포넌트 | S3/ADLS/GCS + Delta Lake | 구조 전환 필요 |
| Hive Metastore | 하둡 컴포넌트 | Unity Catalog metastore | 비교적 직접 대응 |
| Hive on Tez | 하둡 컴포넌트 | SQL Warehouse + Spark Compute | 용도에 따라 분리 |
| Impala | 하둡 컴포넌트 | SQL Warehouse | 1:1에 가장 가까움 |
| Kudu | 하둡 컴포넌트 | Delta Lake | 비교적 직접 대응 |
| Oozie | 하둡 컴포넌트 | Lakeflow Jobs | 1:1에 가장 가까움 |
| Ranger | 하둡 컴포넌트 | Unity Catalog | 비교적 직접 대응 |
| Hue | 하둡 컴포넌트 | Notebook + SQL Editor + Catalog Explorer | UI 기능으로 분화 |
| Tez | 하둡 컴포넌트 | Spark 내부 실행 레이어 | 독립 서비스 없음 |
| YARN | 하둡 컴포넌트 | Databricks 내부 Compute 관리 | 플랫폼이 흡수 |
| YARN Queue Manager | 하둡 컴포넌트 | Compute 정책 + SQL Warehouse 거버넌스 | 유사 기능으로 분화 |
| ZooKeeper | 하둡 컴포넌트 | Databricks 내부 coordination 레이어 | 플랫폼이 흡수 |
| Core Configuration | 하둡 컴포넌트 | Workspace/Compute 설정 | 플랫폼이 흡수 |
| CDP-INFRA-SOLR | 하둡 컴포넌트 | Unity Catalog 감사 + 외부 로그 분석 | 직접 대응 없음 |
| CDE | CDP 상위 서비스 | Workflows (Jobs) + Delta Live Tables | 비교적 직접 대응 |
| CDW | CDP 상위 서비스 | Databricks SQL (Photon) | 비교적 직접 대응 |
| CML | CDP 상위 서비스 | Mosaic AI (MLflow 기반) | 비교적 직접 대응 |
| CDF | CDP 상위 서비스 | Delta Live Tables + Structured Streaming | 일부 기능 차이 |
| SDX | CDP 상위 서비스 | Unity Catalog | 비교적 직접 대응 |

## 플랫폼 선택 가이드

| 상황 | 추천 |
|:---|:---|
| 온프레미스 + 클라우드 병행(하이브리드) 필요 | Cloudera |
| 보안·규제가 엄격하고 사내 서버 필수 | Cloudera |
| 기존 Hadoop 환경에서 점진적 전환 | Cloudera |
| 클라우드 네이티브 환경 | Databricks |
| AI/ML/GenAI가 핵심 | Databricks |
| 인프라 관리 부담을 줄이고 싶음 | Databricks |
| 데이터 엔지니어링+분석을 하나로 통합 | Databricks |
