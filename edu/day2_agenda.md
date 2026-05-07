# Day 2 — MLOps

## 목차
1. [MLOps 개요](#1-mlops-개요)
2. [Databricks 기반 MLOps](#2-databricks-기반-mlops)
3. [Feature Engineering & Gold Table](#3-feature-engineering--gold-table)
4. [Model Training & Tracking](#4-model-training--tracking)
5. [Model Serving](#5-model-serving)
6. [Hands-on Lab](#6-hands-on-lab)

---

## 1. MLOps 개요
- MLOps란 무엇인가 / 왜 필요한가
- ML Lifecycle 이해
  - Data Preparation / Feature Engineering / Training / Validation / Deployment / Monitoring
- Data Engineering과 MLOps의 연결
- 운영 환경에서의 ML 문제점 — 데이터 변경 / 모델 성능 저하 / 재학습 필요성

---

## 2. Databricks 기반 MLOps
- Databricks에서의 ML Workflow
- MLflow 기본 개념
  - Experiment Tracking / Metrics / Parameters / Artifact 저장
- Model Registry 개념
- Unity Catalog와 ML 관리

---

## 3. Feature Engineering & Gold Table
- ML용 데이터셋 구성 방법
- Bronze / Silver / Gold 복습
- Aggregation Gold Table 생성
- 학습용 데이터셋 생성 흐름

---

## 4. Model Training & Tracking
- 기본 ML 모델 생성 및 학습
- MLflow를 활용한 Tracking
- Experiment 관리 방법
- 모델 Registry 등록

---

## 5. Model Serving
- Model Serving 개념 / Real-time Inference 구조
- Databricks Model Serving
- Serving Endpoint 생성
- 운영 환경 배포 흐름 소개

---

## 6. Hands-on Lab

> Day 1에서 구축한 Silver 테이블을 이어받아 Gold → 모델 학습 → 서빙까지 연결하는 흐름으로 진행

**Step 1. Gold Table 생성 (Silver → Gold)**
- Day 1에서 만든 Silver 테이블 확인
- 집계/피처 가공으로 Aggregation Gold Table 생성
- Gold Table을 Delta로 저장 및 Unity Catalog 등록

**Step 2. ML 학습용 Feature Dataset 구성**
- Gold Table에서 학습용 Feature / Label 분리
- Train / Test 데이터셋 분할

**Step 3. 모델 학습 및 MLflow Tracking**
- 기본 ML 모델 학습 (scikit-learn / XGBoost 등)
- MLflow로 Experiment / Metrics / Parameters / Artifact 기록
- 여러 파라미터 조합 실험 및 결과 비교

**Step 4. Model Registry 등록**
- 최적 모델을 Unity Catalog Model Registry에 등록
- 모델 버전 관리 및 Champion 지정

**Step 5. 배치 추론**
- 등록된 모델로 Gold Table 전체 배치 추론 실행
- 추론 결과를 Delta Table로 저장
