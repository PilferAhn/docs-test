# Databricks 교육 커리큘럼 (2.5일)

| Day | 주제 | 방식 |
|-----|------|------|
| Day 1 | Data Engineering | 강의 + 실습 |
| Day 2 | MLOps | 강의 + 실습 |
| Day 3 (반나절) | AI Agent | 강의 + 데모 |

---

## Day 1 — Data Engineering

**강의**
1. Databricks 개요
   - Lakehouse Architecture 개념
   - Data Warehouse vs Data Lake vs Lakehouse
   - Databricks Workspace 구조 (Workspace / Cluster / Notebook / Job / SQL Warehouse)

2. Databricks 핵심 구성요소
   - Delta Lake / Unity Catalog / Databricks Runtime / Medallion Architecture

3. Data Engineering 심화 개념
   - ETL 중심으로의 전환, 파일 포맷 선택 전략
   - 파티셔닝 전략 / 파이프라인 설계 원칙 (멱등성, 재처리 가능성)
   - Medallion Architecture 실무 적용 기준

4. Databricks에서의 Data Engineering
   - Spark 분산 처리 개념 (Driver / Executor)
   - DataFrame / Spark SQL / S3 연동 / Delta Table 관리

5. Spark SQL vs RDB SQL
   - 실행 방식 차이 (인덱스 vs 분산 스캔)
   - 트랜잭션 / JOIN / 미지원 기능 비교
   - Spark SQL의 강점

6. Compute / Cluster 설정
   - Compute 유형 이해 (All-purpose / Job / SQL Warehouse / Serverless)
   - Cluster 생성 — Runtime / Node / Auto Scaling / Auto Termination / Spot vs On-demand
   - 고급 설정 — Spark Config / Init Script / 라이브러리 설치 / Policy / Tags
   - Spark UI 모니터링 / Notebook 연결

**Hands-on Lab**
- Cluster 직접 생성 및 설정
- CSV 데이터 로드 → DataFrame 변환 → Spark SQL 실습
- Delta Table CRUD / Time Travel
- Bronze → Silver 파이프라인 구현

---

## Day 2 — MLOps

**강의**
1. MLOps 개요
   - ML Lifecycle (Data Prep → Feature Engineering → Training → Deployment → Monitoring)
   - Data Engineering과 MLOps의 연결고리
   - 운영 환경에서의 ML 문제점

2. Databricks 기반 MLOps
   - MLflow (Experiment Tracking / Metrics / Artifact 저장)
   - Model Registry / Unity Catalog와 ML 관리

3. Feature Engineering & Gold Table
   - Aggregation Gold Table 생성 / 학습용 데이터셋 구성 흐름

4. Model Training & Tracking
   - MLflow를 활용한 실험 관리 / Model Registry 등록

5. Model Serving
   - Serving Endpoint 개념 / 운영 환경 배포 흐름

**Hands-on Lab**
> Day 1 Silver 테이블을 이어받아 Gold → 모델 학습 → 배치 추론까지 연결

- Silver → Gold Aggregation Table 생성 및 Unity Catalog 등록
- Feature / Label 분리 및 Train / Test 분할
- ML 모델 학습 + MLflow Tracking (Metrics / Params / Artifact)
- Model Registry 등록 및 Champion 지정
- Gold Table 전체 배치 추론 → 결과 Delta Table 저장

---

## Day 3 (반나절) — AI Agent

> Hands-on 없음 — 강의 + 데모 시연

**강의**
1. AI Agent 기초 개념
   - LLM 기반 Agent 구조 / RAG 개념 / Tool Calling / Databricks Mosaic AI 소개

2. Mosaic AI Vector Search
   - Embedding 개념 / 유사도 vs 키워드 vs 하이브리드 검색
   - Vector Search Index 유형 3가지 (Managed / Self-managed / Direct Vector Access)

3. LangGraph 개요
   - State / Node / Edge / Graph Builder 핵심 개념
   - 주요 패턴 (Linear Flow / Router / Fan-out / Conditional Loop / Tool-Driven)

**데모 시연**
- Vector Search Index 생성 및 동기화
- ChatDatabricks + DatabricksVectorSearch 연동
- LangGraph Agent 동작 흐름
