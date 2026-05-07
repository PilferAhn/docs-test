# Day 1 — Data Engineering

## 목차
1. [Databricks 개요](#1-databricks-개요)
2. [Databricks 핵심 구성요소](#2-databricks-핵심-구성요소)
3. [Data Engineering 기본 개념](#3-data-engineering-기본-개념)
4. [Databricks에서의 Data Engineering](#4-databricks에서의-data-engineering)
5. [Compute / Cluster 설정](#5-compute--cluster-설정)
6. [Hands-on Lab](#6-hands-on-lab)

---

## 1. Databricks 개요
- Databricks란 무엇인가
- 왜 사용하는가
- Lakehouse Architecture 개념
- Data Warehouse vs Data Lake vs Lakehouse
- Databricks Workspace 구조
  - Workspace / Cluster / Notebook / Job / Repo / SQL Warehouse

---

## 2. Databricks 핵심 구성요소
- Delta Lake — 데이터를 안전하게 저장하는 Databricks의 기본 파일 포맷
- Unity Catalog — 데이터 자산을 한 곳에서 통합 관리하는 거버넌스 시스템
- Databricks Runtime — 클러스터 실행 환경 (Spark + 라이브러리 묶음)
- Medallion Architecture — 데이터 품질 단계별 분리 (Bronze → Silver → Gold)

---

## 3. Data Engineering 심화 개념
- ELT 중심으로의 전환 — 왜 Databricks에서는 ELT가 표준인가
- Batch vs Micro-batch vs Streaming — 선택 기준과 트레이드오프
- 파일 포맷 선택 전략 — Parquet vs Delta, 언제 무엇을 쓰는가
- 파티셔닝 전략 — 과도한 파티셔닝의 문제 (Small File Problem)
- 데이터 파이프라인 설계 원칙 — 멱등성(Idempotency), 재처리 가능성
- Medallion Architecture 심화 — Bronze/Silver/Gold 경계 기준과 실무 적용

---

## 4. Databricks에서의 Data Engineering
- Notebook 기반 개발 방식
- Spark 기본 개념 — Driver / Executor / Distributed Processing
- DataFrame 기본 사용 / Spark SQL 기본
- AWS S3 연동 및 데이터 Ingest 개념
- Delta Table 생성 및 관리

---

## 5. Compute / Cluster 설정
> 실습 전 직접 클러스터를 생성하고 설정하는 과정을 다룬다

- Compute 유형 이해
  - All-purpose Cluster — 개발/탐색용, 대화형 노트북 실행
  - Job Cluster — 자동화된 Job 실행 전용, 실행 후 자동 종료
  - SQL Warehouse — SQL 분석 전용 컴퓨팅
  - Serverless Compute — 인프라 관리 없이 즉시 사용

- Cluster 생성 실습
  - Cluster 생성 화면 구성 이해
  - Cluster 이름 / Access Mode 설정
  - Databricks Runtime 버전 선택 기준
  - Worker / Driver Node 타입 및 수량 설정
  - Auto Scaling 설정 — 최소/최대 Worker 수
  - Auto Termination 설정 — 유휴 시 자동 종료
  - Spot Instance vs On-demand 차이

- Cluster 고급 설정
  - Spark Config 추가 (환경변수, 튜닝 파라미터)
  - Init Script — 클러스터 시작 시 자동 실행 스크립트
  - 라이브러리 설치 (PyPI / Maven / DBFS)
  - Cluster Policy — 조직 내 사용 규칙 적용
  - Cluster Tags — 비용 추적을 위한 태그 설정

- Cluster 운영
  - Cluster 상태 확인 (Running / Terminated / Pending)
  - Cluster Event Log — 이벤트 및 오류 확인
  - Spark UI — Job / Stage / Task 모니터링
  - Cluster 재시작 / 종료 / 삭제

- Notebook과 Cluster 연결
  - Notebook에 Cluster 연결하는 방법
  - 여러 Notebook에서 동일 Cluster 공유
  - Detach / Reattach 시 주의사항

---

## 6. Hands-on Lab
- Cluster 직접 생성 및 설정
- Notebook 작성 및 Cluster 연결
- CSV 데이터 로드 (inferSchema / 명시적 스키마)
- DataFrame 변환 실습 — select / filter / groupBy / join
- Spark SQL 실습 — Temp View 등록, SQL 쿼리
- Delta Table CRUD (INSERT / UPDATE / DELETE / MERGE)
- Time Travel 실습
- Bronze → Silver 파이프라인 구현
- 실습용 데이터베이스는 별도 제공 예정
