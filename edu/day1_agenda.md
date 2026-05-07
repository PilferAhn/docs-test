# Day 1 — Data Engineering

## 목차
1. [Databricks 개요](#1-databricks-개요)
2. [Databricks 핵심 구성요소](#2-databricks-핵심-구성요소)
3. [Data Engineering 기본 개념](#3-data-engineering-기본-개념)
4. [Databricks에서의 Data Engineering](#4-databricks에서의-data-engineering)
5. [Hands-on Lab](#5-hands-on-lab)

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
- Delta Lake
  - ACID Transaction / Schema Enforcement / Time Travel
- Unity Catalog
  - Catalog / Schema / Table 구조
  - 권한 관리 기본 / Data Governance 개념
- Databricks Runtime
- Medallion Architecture — Bronze / Silver / Gold

---

## 3. Data Engineering 기본 개념
- Data Engineering 역할
- ETL / ELT 차이
- Batch vs Streaming
- 데이터 파이프라인 기본 개념
- 파일 포맷 기초 — CSV / Parquet / Delta

---

## 4. Databricks에서의 Data Engineering
- Notebook 기반 개발 방식
- Cluster 기본 이해 — Interactive / Job / Photon
- Spark 기본 개념 — Driver / Executor / Distributed Processing
- DataFrame 기본 사용 / Spark SQL 기본
- AWS S3 연동 및 데이터 Ingest 개념
- Delta Table 생성 및 관리

---

## 5. Hands-on Lab
- Databricks 환경 및 Cluster 접속
- Notebook 작성 및 실행
- CSV 데이터 로드 (inferSchema / 명시적 스키마)
- DataFrame 변환 실습 — select / filter / groupBy / join
- Spark SQL 실습 — Temp View 등록, SQL 쿼리
- Delta Table CRUD (INSERT / UPDATE / DELETE / MERGE)
- Time Travel 실습
- Bronze → Silver 파이프라인 구현
- 실습용 데이터베이스는 별도 제공 예정
