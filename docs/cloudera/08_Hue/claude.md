# Hue (Claude 정리)

> GPT 답변 + Gemini 답변을 종합 정리한 버전

## Hue란?

**웹 브라우저에서 SQL을 작성하고 데이터를 탐색하는 UI 도구**입니다.

운영자가 아닌 데이터 분석가나 엔지니어들이 복잡한 터미널 명령 없이 쉽게 클러스터를 활용할 수 있는 **포털 역할**을 합니다.

## Cloudera에서의 역할

GPT 관점:
- 브라우저에서 SQL 편집, 실행, 결과 확인
- Hive/Impala/HDFS 탐색
- 클러스터 서비스들의 **게이트웨이** 역할
- 실제 권한은 Ranger가 제어 (Hue는 UI만 제공)

Gemini 관점:
- CDW에서 분석가가 SQL을 작성하는 도구
- Databricks에서는 외부 BI 도구(Tableau, Power BI) 연결로 대체하는 경향

## Databricks 대응

Hue의 기능이 **여러 UI 기능으로 분화**되어 있습니다.

| Hue 기능 | Databricks 대응 |
|:---|:---|
| SQL 작성·실행 | **SQL Editor** |
| 쿼리 저장·공유 | SQL Editor 내 저장 기능 |
| 데이터/테이블 탐색 | **Catalog Explorer** |
| HDFS 파일 탐색 | Catalog Explorer (Volumes) |
| 엔지니어링 작업 | **Notebook UI** |
| 간단한 시각화 | **Lakeview 대시보드** |
| BI 도구 연결 | **Partner Connect** (Tableau, Power BI 등) |

### 중요한 차이
Cloudera에서는 Hue가 "하나의 통합 포털"이었지만,
Databricks에서는 기능별로 분화된 UI를 각각 사용합니다.
Gemini가 지적하듯, Databricks는 내부 UI보다 **외부 BI 도구 생태계**를 더 강조합니다.

## 한 줄 요약

**Hue ≈ Notebook + SQL Editor + Catalog Explorer**
(단일 서비스 대응이 아닌 UI 기능 분화)
