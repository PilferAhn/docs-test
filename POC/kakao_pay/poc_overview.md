# Kakao Pay — Databricks PoC 전체 설계 문서

> **목적:** Cloudera/온프레미스/Hadoop 기반 데이터 플랫폼을 Databricks Lakehouse로 전환할 수 있는지 검증
> **성격:** 단순 마이그레이션 검증이 아닌 **전사 데이터·AI 플랫폼 대체 가능성 종합 검증**

---

## 목차

1. [AS-IS 현황 (현재 자산)](#1-as-is-현황)
2. [PoC 목적 및 범위](#2-poc-목적-및-범위)
3. [시나리오 A — 데이터 적재 / 마이그레이션](#3-시나리오-a--데이터-적재--마이그레이션)
4. [시나리오 B — ETL / 배치 파이프라인 전환](#4-시나리오-b--etl--배치-파이프라인-전환)
5. [시나리오 C — 성능 비교](#5-시나리오-c--성능-비교)
6. [시나리오 D — SQL Warehouse / BI 연동](#6-시나리오-d--sql-warehouse--bi-연동)
7. [시나리오 E — 실시간 조회 / 서빙](#7-시나리오-e--실시간-조회--서빙)
8. [시나리오 F — Delta Live Tables / Streaming Table](#8-시나리오-f--delta-live-tables--streaming-table)
9. [시나리오 G — 스키마 변경](#9-시나리오-g--스키마-변경)
10. [시나리오 H — CDC 처리](#10-시나리오-h--cdc-처리)
11. [시나리오 I — 탈퇴자 삭제 / 컴플라이언스](#11-시나리오-i--탈퇴자-삭제--컴플라이언스)
12. [시나리오 J — 보안 / 권한 / 컴플라이언스](#12-시나리오-j--보안--권한--컴플라이언스)
13. [시나리오 K — 인프라 / 클라우드 구성](#13-시나리오-k--인프라--클라우드-구성)
14. [시나리오 L — 데이터 이관](#14-시나리오-l--데이터-이관)
15. [시나리오 M — 데이터 아키텍처 / 저장 포맷](#15-시나리오-m--데이터-아키텍처--저장-포맷)
16. [시나리오 N — 비용 / TCO 최적화](#16-시나리오-n--비용--tco-최적화)
17. [시나리오 O — 모니터링 / 관제](#17-시나리오-o--모니터링--관제)
18. [시나리오 P — DS / MLOps](#18-시나리오-p--ds--mlops)
19. [보조 시트 요약](#19-보조-시트-요약)
20. [핵심 리스크](#20-핵심-리스크)
21. [PoC 우선순위 권장](#21-poc-우선순위-권장)
22. [최종 요약](#22-최종-요약)

---

## 1. AS-IS 현황

> 현재 카카오페이가 운영 중인 데이터 플랫폼 자산

### 플랫폼 구성

```
Cloudera (온프레미스 Hadoop 기반)
├── Hive Metastore       ← 테이블 스키마/경로 정보 저장소 (MySQL 기반)
├── Hive Table           ← HDFS 위에 SQL로 접근하는 테이블
├── Kudu Table           ← Cloudera 전용 컬럼형 스토리지 (실시간 UPDATE 지원)
└── Impala               ← 빠른 SQL 쿼리 엔진 (Hive보다 빠름)

Iceberg / Tiara
├── HDFS External Table  ← HDFS 파일을 테이블처럼 접근 (파일 삭제 안 됨)
└── Hive Metastore       ← 스키마 정보 공유

MSTR                     ← MicroStrategy, BI(Business Intelligence) 시각화 도구
Airflow                  ← 데이터 파이프라인 스케줄링/워크플로우 관리 도구
DataHub                  ← 데이터 카탈로그 (어떤 데이터가 어디 있는지 관리)
```

---

## 2. PoC 목적 및 범위

> "현재 Cloudera에서 돌고 있는 데이터 적재, ETL, 분석, BI, ML, 보안, 운영 체계를
> Databricks로 옮겨도 문제없이 돌아가는가?"

### 검증 전체 범위

| 영역 | 검증 항목 |
|:---|:---|
| 데이터 이관 | Hive/Kudu/Iceberg/HDFS → Delta/S3 |
| 실시간 스트리밍 | Kafka → Delta Lake Structured Streaming |
| CDC 처리 | MySQL binlog → Kafka → DLT |
| 배치 ETL | 36TB 파이프라인 전환 |
| SQL 성능 | Impala/Trino vs Databricks SQL/Photon |
| BI 연동 | MSTR ↔ Databricks SQL Warehouse |
| 보안/권한 | Unity Catalog, Row Filtering, Column Masking |
| 컴플라이언스 | GDPR 탈퇴자 삭제, Audit Log |
| Airflow 연동 | Databricks Operator 호환성 |
| Delta Lake 전환 | 포맷 비교, Liquid Clustering |
| ML/MLOps | Feature Store, 분산 학습, Batch/Real-time Inference |
| GPU 학습 | 탄력적 GPU 할당 |
| 비용/TCO | Spot Instance, Serverless vs Classic, OPTIMIZE/VACUUM |
| 모니터링 | Grafana, CloudWatch, Slack 알람 |
| Unity Catalog 거버넌스 | 리니지 추적, 권한 분리 |

---

## 3. 시나리오 A — 데이터 적재 / 마이그레이션

---

### A-1. Kafka → Delta Lake (실시간 적재)

> **티아라(Tiara):** 카카오페이 내부 행동 로그 시스템

**목표:** 티아라 행동로그를 Kafka에서 받아 Databricks Delta Lake에 실시간 적재

**데이터 규모**

```
티아라 로그
├── 230GB / day
├── 75개 컬럼
└── 1개월 ≈ 7TB
```

**검증 항목**

```
처리 성능
├── 초당 4.5만 건 처리 가능 여부
└── CDC → Kafka → Structured Streaming → Delta Lake 전체 지연시간 측정

데이터 정합성
├── Exactly-Once 보장           ← 중복 없이 정확히 한 번만 처리
├── pay_account_id 실시간 보강  ← 스트리밍 중 다른 테이블과 조인
└── Upsert / Merge 검증         ← 동일 키 데이터 들어올 때 업데이트 처리

운영 안정성
├── 장애 복구 방안
├── Small File 문제 확인        ← 스트리밍 시 작은 파일 수백만 개 생기는 문제
├── Optimize / Compaction 주기  ← 작은 파일 병합 주기 최적화
└── 탈퇴자 삭제 쿼리 성능 영향도
```

**성공 기준:** 기존 NiFi 또는 Flink와 동등 이상

---

### A-2. Iceberg → Parquet → Delta 전환

> **Iceberg:** Netflix가 만든 오픈소스 테이블 포맷, ACID 트랜잭션 지원

**목표:** 기존 Iceberg 데이터를 Spark으로 읽어 Parquet/Delta로 전환

**대상 테이블**
- `tiara_complete_log_raw`
- `tiara_ns`

**데이터 범위:** 10/20 ~ 10/26

---

### A-3. Kudu → Delta 전환

> **Kudu:** Cloudera 전용 컬럼형 스토리지, 실시간 INSERT/UPDATE/DELETE 지원
> **Spark Connector:** Kudu 데이터를 Spark으로 읽기 위한 라이브러리

**목표:** Kudu 테이블을 Spark Connector로 읽어 Delta로 전환

**대상 테이블 및 범위**

| 테이블 | 데이터 범위 |
|:---|:---|
| an005d04 | 2024/10/01 ~ 10/26 |
| bp501d01 | 2025/01/01 ~ 10/26 |

**핵심 검증:** Kudu + Impala 기반 조회/처리를 Delta + Databricks SQL로 대체 가능한가

---

## 4. 시나리오 B — ETL / 배치 파이프라인 전환

> **ETL:** Extract(추출) → Transform(변환) → Load(적재), 데이터 가공 파이프라인

**목표:** 현재 Hive, Kudu, Tiara 기반 ETL을 Databricks로 이전

**데이터 규모**

```
총 데이터 사이즈  ≈ 36TB
총 테이블 수      45개
대상 도메인       티아라, 마이데이터, 결제, 머니
데이터 기간       최근 1개월
```

**기존 병목 포인트**

```
Impala row_number 병목   ← 순위 함수가 대용량에서 느림
Aggregation 병목         ← 집계 쿼리 처리 속도
Heavy UDF                ← 사용자 정의 함수 성능 문제
JSON Parsing 작업        ← 비정형 JSON 컬럼 파싱 속도
```

**검증 항목**

```
연결 및 추출
변환 및 가공
배치 파이프라인 전환
Airflow Databricks Operator 호환성    ← 기존 Airflow DAG 재사용 가능한가
Databricks Workflow 사용성
Databricks Lakeflow / SDP 검토        ← Databricks 자체 파이프라인 도구
데이터 품질 로깅 및 모니터링
```

---

## 5. 시나리오 C — 성능 비교

> **Photon:** Databricks 자체 개발 벡터화 쿼리 엔진, C++ 기반으로 Spark보다 빠름
> **TPC-H:** 데이터베이스 성능 표준 벤치마크 테스트

**비교 대상**

```
기존                    신규
─────────────────────────────────────
Cloudera Impala    vs   Databricks SQL
Trino              vs   Databricks Photon
StarRocks          vs   Delta Lake
Ceph               vs   Managed/External Iceberg
```

**주요 테스트 항목**

| 테스트 | 내용 |
|:---|:---|
| Top 5 쿼리 성능 비교 | 실제 운영 쿼리 기준 |
| 배치 Top 5 쿼리 성능 비교 | 배치 작업 기준 |
| TPC-H 1TB 벤치마크 | 표준 성능 지표 |
| Trino vs Databricks | 쿼리 엔진 직접 비교 |
| Photon On/Off 비교 | Photon 엔진 효과 측정 |
| Classic vs Serverless SQL Warehouse | 운영 방식별 성능 비교 |
| 동시 사용자 쿼리 성능 | 동시 접속 100명 이상 |
| Auto-scaling 성능 | 부하 증가 시 자동 확장 |
| 인스턴스 타입별 성능 | 서버 사양별 비교 |

> **현재 상태:** `쿼리 성능 테스트` 시트는 헤더(DML / SQL warehouse / DBX 성능 / 기존 성능)만 있는 템플릿 상태 → 실제 수치 채워야 함

---

## 6. 시나리오 D — SQL Warehouse / BI 연동

> **MSTR (MicroStrategy):** 기업용 BI 시각화 도구
> **Service Principal:** 사람이 아닌 애플리케이션/서비스가 인증할 때 쓰는 계정 개념
> **SQL Warehouse:** Databricks에서 SQL 쿼리를 실행하는 전용 컴퓨팅 리소스

**목표:** 기존 MSTR BI 사용자가 Databricks SQL Warehouse를 통해 기존처럼 안정적으로 조회할 수 있는가

**검증 항목**

```
인증/연결 설정
├── Service Principal 생성
├── SP 토큰 생성
├── SP 권한 관리
└── Unity Catalog 연결

조회 성능
├── 카탈로그/스키마/테이블 조회
├── 큐브 쿼리 성능              ← MSTR 큐브: 사전 집계된 다차원 데이터 구조
├── 집계 쿼리 수행 성능
└── Databricks SQL 사용 시 서버 리소스 모니터링
```

---

## 7. 시나리오 E — 실시간 조회 / 서빙

> **OLAP (Online Analytical Processing):** 대용량 데이터 분석용 쿼리 처리
> **콜드 스타트:** 클러스터가 꺼져 있다가 처음 켜질 때 걸리는 초기화 시간
> **StarRocks:** 초저지연 실시간 OLAP 엔진 (100ms 미만 응답 목표)

**목표:** Databricks SQL Warehouse를 실시간 서빙 용도로 사용할 수 있는가

**검증 항목**

```
응답 성능
├── API 응답 속도
├── 콜드 스타트 시간
└── 실시간 적재 중 조회 응답 시간 (기존 대비 150% 이내)

안정성
├── 동시 접속 100명 이상
├── 조회 실패율
└── 수집 지연 여부
```

**비교 기준**

| 엔진 | 목표 응답 시간 |
|:---|:---:|
| StarRocks | 100ms 미만 |
| Databricks SQL Warehouse | 비교 대상 |

> **주의:** Databricks SQL Warehouse는 분석/BI/대화형 SQL에 강하나,
> 초저지연 OLAP 서빙은 워크로드에 따라 별도 검증 필요

---

## 8. 시나리오 F — Delta Live Tables / Streaming Table

> **DLT (Delta Live Tables):** Databricks 자체 스트리밍/배치 파이프라인 프레임워크, 선언형으로 작성
> **Materialized View (MV):** 쿼리 결과를 미리 계산해서 저장해두는 가상 테이블
> **Compaction:** 작은 파일들을 하나의 큰 파일로 병합하는 작업

**검증 항목**

```
성능
├── Streaming Table 적재 성능
└── Streaming Table ↔ Materialized View 동기화 성능

정합성
├── 탈퇴자 삭제 후 Compaction 시 변경사항 추적 이슈
├── MV 재구축 시간
└── 외부 Spark 적재 방식 vs DLT 방식 리소스/성능 비교
```

---

## 9. 시나리오 G — 스키마 변경

> **온라인 스키마 변경:** 서비스 중단 없이 테이블 구조를 바꾸는 것
> **DDL (Data Definition Language):** 테이블 구조를 정의/변경하는 SQL (CREATE, ALTER, DROP)

**핵심 질문:** 대용량 7TB 테이블에 대해 무중단 스키마 변경이 가능한가?

**검증 항목**

```
변경 종류
├── 컬럼 추가
├── 컬럼 삭제
└── 타입 변경

운영 영향
├── 수집 지연 없음
├── 조회 영향 없음
└── 무중단 처리
```

**성공 기준:** DDL 완료 1시간 이내

> **기존 문제:** Pinot에서 동일 작업 시 24시간 소요

---

## 10. 시나리오 H — CDC 처리

> **CDC (Change Data Capture):** DB 변경사항(INSERT/UPDATE/DELETE)을 실시간으로 캡처하는 기술
> **binlog:** MySQL 변경 이력 로그 파일
> **Minecraft:** 내부 CDC 파이프라인 도구 (추정)
> **Exactly-Once:** 메시지가 정확히 한 번만 처리됨을 보장 (중복/누락 없음)
> **Schema Evolution:** 스키마 변경 시 기존 데이터와 자동 호환 처리

**시나리오:** MySQL binlog → Minecraft → Kafka → DLT CDC

**데이터 규모**

```
결제 초당 600건
Kafka lag 12시간 누적 ≈ 2,600만 건
```

**검증 항목**

```
데이터 처리
├── Insert 처리
├── Update 처리
├── Delete 처리
├── 데이터 변경 순서 보장
└── Schema Evolution 자동 처리

안정성
├── Exactly-Once 보장
└── Kafka lag 12시간 누적 후 복구 검증
```

---

## 11. 시나리오 I — 탈퇴자 삭제 / 컴플라이언스

> **GDPR:** 유럽 개인정보보호 규정, 탈퇴 시 24시간 이내 삭제 의무
> **MVCC (Multi-Version Concurrency Control):** 삭제/수정 중에도 다른 쿼리가 이전 버전 읽을 수 있게 보장
> **0-byte Parquet 방어:** 삭제 후 빈 파일이 생겨 쿼리 오류 나는 현상 방어

> **이 시나리오가 PoC에서 가장 중요한 항목 중 하나**
> Delta Lake가 대용량 개인정보를 안전하고 빠르게 삭제할 수 있는가가 도입 판단의 핵심

### 1개월 데이터 삭제 테스트

```
데이터 크기  : 1개월 225GB
탈퇴자 PK   : 1만 건
목표         : GDPR 기준 24시간 이내 삭제 완료
```

**검증 항목**

```
├── 삭제 중 조회 정합성 검증
├── MVCC 보장
├── 0-byte Parquet 방어
└── 실시간 수집과 삭제 동시 실행 시 충돌 검증
```

### 1년 데이터 삭제 테스트

```
데이터 크기  : 1년 84TB
탈퇴자 PK   : 12만 건
목표         : 48시간 이내 삭제 완료
```

**검증 항목**

```
├── 파티션 병렬 삭제 가능 여부
└── 삭제 중 서비스 영향도
```

---

## 12. 시나리오 J — 보안 / 권한 / 컴플라이언스

> **Unity Catalog:** Databricks 통합 데이터 거버넌스 플랫폼 (테이블/권한/리니지 통합 관리)
> **Row Filtering:** 특정 사용자에게 특정 행만 보이게 제한
> **Column Masking:** 특정 컬럼을 마스킹(가림) 처리
> **Service Principal:** 사람이 아닌 시스템/앱이 인증할 때 쓰는 계정
> **QueryPie:** 데이터 접근 통제 및 감사 도구
> **Audit Log:** 누가 언제 어떤 데이터에 접근했는지 기록
> **샤카:** 내부 사전 승인 시스템 (추정)

### 접근 통제

```
├── SQL Editor 접근 통제
├── 식별DB 접근 차단 / 분석DB만 허용
├── 조회 사유 선입력
├── Audit Log 기록
├── Notebook Export 사후 승인
└── QueryPie 연동
```

### 배치 승인

```
├── Workflow 컴플라이언스
├── 샤카 사전승인 API 연동
├── 실패 Job 승인 관리
└── Audit Log 기록
```

### Unity Catalog 기반 권한

```
카탈로그 분리
├── 분석용 catalog    ← 마스킹된 데이터
└── 식별용 catalog    ← 원본 데이터 (제한적 접근)

권한 제어
├── 그룹별 Read/Write 권한 분리
├── Row Filtering
├── Column Masking
└── Apache Ranger 대체 가능성 검증   ← 현재 Cloudera 보안 도구
```

---

## 13. 시나리오 K — 인프라 / 클라우드 구성

> **Keycloak:** 오픈소스 SSO(Single Sign-On) 인증 서버
> **Kerberos:** 네트워크 인증 프로토콜, Hadoop 클러스터 보안에 표준
> **Keytab:** Kerberos 인증 자격증명 파일
> **kinit:** Kerberos 티켓 발급 명령어
> **KDC (Key Distribution Center):** Kerberos 인증 서버
> **UniForm:** Delta/Iceberg/Hudi 포맷 간 상호운용성 지원하는 Databricks 기능

### AWS 클라우드 구성

```
S3 버킷 분리
├── DBFS (Databricks File System)
├── Unity Catalog
└── External

네트워크
├── S3 Gateway Endpoint   ← S3 트래픽을 인터넷 경유 없이 내부망으로 처리
└── 버킷 정책
```

### 인증/접근 관리

```
SSO 연동
└── Keycloak ↔ AWS SSO ↔ Databricks SSO

권한 제어
├── Service Principal 생성
├── Workspace / Cluster 생성 권한 제어
└── GitHub ↔ Databricks Git Folder 연동
```

### 온프레미스 연동 (하이브리드)

```
Hadoop 연결
├── Kerberos 연동
├── Keytab → Databricks Secrets 등록
├── Init Script로 kinit 수행    ← 클러스터 시작 시 자동 인증
└── HDFS 접근용 KDC 인증

메타스토어 연동
├── 온프렘 Hive Metastore / HMS External 등록
├── Trino에서 Databricks UC 질의
└── UniForm + Trino Iceberg Connector 검증
```

---

## 14. 시나리오 L — 데이터 이관

> **DistCp:** Hadoop 분산 복사 도구, HDFS 간 또는 HDFS→S3 대용량 파일 복제에 사용
> **QoS (Quality of Service):** 네트워크 대역폭 품질 보장

**이관 방식**

```
방식 1: DistCp
HDFS → S3 직접 복제 (대용량 권장)
hadoop distcp hdfs:///warehouse/.../  s3a://bucket/...

방식 2: Databricks
S3 적재 후 Delta 포맷으로 변환
```

**검증 항목**

```
├── 네트워크 대역폭 병목 확인
├── QoS 영향도
├── 포맷 변환 소요 시간 (Parquet → Delta)
└── 초기 마이그레이션 파이프라인 완성 여부
```

---

## 15. 시나리오 M — 데이터 아키텍처 / 저장 포맷

> **Delta Lake:** Databricks가 만든 오픈소스 저장 포맷, Parquet 기반 + ACID 트랜잭션
> **Managed Iceberg:** Databricks가 관리하는 Iceberg 테이블
> **UniForm:** Delta/Iceberg/Hudi 포맷 통합 호환 레이어
> **Liquid Clustering:** Delta Lake의 동적 데이터 클러스터링 (Z-ORDER 대체)
> **Deletion Vectors:** Delta Lake 삭제 최적화, 파일 재작성 없이 삭제 마킹
> **행 수준 동시성:** 같은 파일의 다른 행을 동시에 수정 가능

**포맷 비교 대상**

| 포맷 | 특징 |
|:---|:---|
| Delta Lake Native | Databricks 표준, ACID 완전 지원 |
| Managed Iceberg | Databricks 관리형, 외부 엔진 호환 |
| External Iceberg | 직접 관리, 유연성 높음 |
| UniForm | Delta/Iceberg 동시 지원 |
| Parquet | 범용 포맷, ACID 없음 |

**검증 항목**

```
성능
├── Delta Lake vs Managed Iceberg 쓰기/읽기 성능
├── Metadata 생성 오버헤드
├── Databricks 단일 엔진 내 쿼리 성능
├── CRUD 성능
└── 다차원 검색 성능

최적화
├── Liquid Clustering 적용 기준
├── Deletion Vectors
└── 행 수준 동시성
```

---

## 16. 시나리오 N — 비용 / TCO 최적화

> **TCO (Total Cost of Ownership):** 총 소유 비용 (초기 구축 + 운영 비용 합산)
> **Spot Instance:** AWS 여유 자원을 저렴하게 쓰는 인스턴스 (최대 90% 할인, 중단 가능)
> **DBU (Databricks Unit):** Databricks 과금 단위
> **VACUUM:** Delta Lake에서 오래된 파일 삭제해 스토리지 회수
> **OPTIMIZE / Z-ORDER:** 파일 병합 + 데이터 정렬로 쿼리 성능 향상
> **S3 Standard-IA:** 자주 접근 안 하는 데이터용 저렴한 S3 스토리지 클래스

**핵심 질문:** Databricks가 단순히 빠른 게 아니라, 실제 총비용이 줄어드는가?

**검증 항목**

```
클러스터 비용 최적화
├── Cluster Policy           ← 클러스터 설정 강제로 비용 통제
├── 비용 태그 강제
├── Spot Instance 활용
├── Job Cluster + Spot + No Pool
├── All-Purpose Cluster + Instance Pool
├── Auto-scaling
└── Auto-termination

SQL Warehouse 비용
├── Classic vs Serverless SQL Warehouse
└── Photon On/Off ROI

스토리지 비용
├── S3 Standard → Standard-IA 전환
├── Glacier Deep Archive        ← 장기 보관용 최저가 스토리지
├── VACUUM으로 스토리지 회수
└── OPTIMIZE / Z-ORDER로 Small File 통제
```

---

## 17. 시나리오 O — 모니터링 / 관제

> **UC System Tables:** Unity Catalog 내 운영 메타데이터 테이블 (쿼리 이력, 비용, 접근 로그)
> **Lineage:** 데이터가 어디서 와서 어디로 갔는지 추적
> **Prometheus / JMX:** 메트릭 수집 도구
> **JVM Heap:** Java 가상머신 메모리 영역

**목적:** Databricks를 사내 중앙 관제 체계에 연동할 수 있는가

**검증 항목**

```
Databricks 내부 관제
├── UC System Tables 활성화
├── Billing / Audit 조회
├── QueryPie 연동
└── Unity Catalog Lineage 자동 추적

알람
└── Workflow 실패 시 Slack 알람

외부 모니터링 연동 (Grafana)
├── Databricks SQL
├── AWS CloudWatch
├── Prometheus / JMX
└── Spark Shuffle / GC / JVM Heap 모니터링
```

---

## 18. 시나리오 P — DS / MLOps

> **BM Index:** 내부 머신러닝 모델 이름 (추정)
> **LAL (Look-Alike):** 기존 고객과 유사한 신규 타겟 찾는 광고 ML 모델
> **Feature Store:** ML 모델에 쓰이는 피처(입력값)를 중앙에서 관리/서빙하는 시스템
> **MLflow:** ML 실험 추적, 모델 버전 관리 오픈소스 도구
> **FAISS:** Meta가 만든 벡터 유사도 검색 라이브러리
> **CTR Prediction:** 광고 클릭률 예측 모델
> **Vector Search:** 벡터 임베딩 기반 유사 아이템 검색

---

### P-1. 기존 ML 파이프라인 이관 (BM Index)

**목표:** BM Index 모델 2개의 training/inference 파이프라인을 Databricks로 이관 가능한지 확인

**데이터 규모**

```
대상 유저   : 2,000만 명
Feature 수  : 약 200개
모델 수     : 2개
```

**검증 항목**

```
Training 파이프라인
├── Airflow 기반 파이프라인 관리
├── MLflow 기반 모니터링
├── 분산 학습 (PyTorch / XGBoost / LightGBM)
└── GPU 활용

Inference 파이프라인
├── 2,000만 유저 × 2개 모델 배치 추론
└── 온라인/오프라인 Feature Store 구성 가능성
```

---

### P-2. 신규 LAL PoC

**목표:** 신규 LAL 모델 Databricks 운영 가능 여부 확인

**데이터 규모**

```
대상 유저   : 2,000만 명 × n개 feature
확장 목표   : 10만 → 100만 → 1,000만+ 유저
```

**검증 항목**

```
Feature Store
├── 광고 Feature Store 테스트
├── 임베딩 적재 지원
└── Vector Search / FAISS 가능성

모델 운영
├── 지속 학습 파이프라인
├── 타겟 추출 API
└── CTR Prediction 실시간 서빙 (100ms 이내)
```

---

## 19. 보조 시트 요약

### 1. PoC 일정계획

현재 템플릿 상태 (컬럼 구조만 있고 실제 일정 미입력)

| 컬럼 | 설명 |
|:---|:---|
| No. / 구분 / 내용 | 시나리오 식별 |
| 데이터브릭스 담당자 | Databricks 측 담당 |
| 고객사 담당자 | 카카오페이 측 담당 |
| 예상 소요 기간 / 일정 | 미입력 상태 |

---

### 2. 데이터엔지니어링

> 검증 체크리스트 시트 (요구사항/검증결과 대부분 미입력 상태)

주요 항목:

```
인프라       클러스터 생성, 온디맨드/스팟, 액세스 모드, Graviton 활용
데이터 처리  정형/반정형/스트리밍, 파티셔닝, Small File, 증분 적재
데이터 관리  History Table, 리니지, DML, Upsert, 마스킹, 스키마 변경
운영         Git 연동, 스케줄 잡, 알림, SLA, 모니터링, 동시성, 권한, SSO
```

---

### 3. SQL 웨어하우스

SQL / Dashboard / Alert / Notebook 항목 포함, 상세 요구사항 미입력 상태 (템플릿)

---

### 4. DSMLOps

> 상세도가 높은 시트, 실무적으로 잘 정리됨

핵심 항목:

```
ML 환경      ML Runtime, 리소스 관리, Legacy Model Import
데이터 연결  Kudu/Hive 온프렘 연결, 대용량 전처리
학습         분산 학습, PyTorch/XGBoost/LightGBM, GPU 탄력 할당
MLOps        MLflow, Databricks Workflows, Airflow 연동, Model Registry
추론         대규모 Batch Inference, Real-time Model Serving
거버넌스     Unity Catalog 기반 리니지
확장성       LLM / Vector DB / RAG 가능성, 벤더 Lock-in 방지
```

---

### 5. 데이터분석

분석가 관점의 검증 항목

```
환경         Jupyter Notebook 분석 리소스 관리
SQL 호환성   Impala SQL 문법 호환성 확인
분석 유연성  SQL ↔ Python/PySpark 전환
파이프라인   Parquet → Delta Lake 전환, Airflow 연동
정리         Delta VACUUM을 통한 임시 테이블 정리
```

**테스트 케이스**

```
일반 워크로드    KPI 파이프라인 이관
복잡한 워크로드  데이터 분석 마트 + Feature Store + 대규모 모델 Inference
```

---

## 20. 핵심 리스크

---

### 리스크 1: 범위 과대

```
이 PoC가 검증하는 것
├── 데이터 플랫폼 전환
├── 실시간 처리 전환
├── BI 전환
├── 보안/권한 전환
├── ML 플랫폼 전환
├── 비용 최적화
└── 관제 연동

→ 한 번에 다 하면 일정/품질 리스크 매우 높음
→ 시나리오 우선순위 설정 필수
```

---

### 리스크 2: 실시간 서빙 성능 목표

```
StarRocks 비교 기준: 100ms 미만
Databricks SQL Warehouse: 분석/BI에 강함, 초저지연 OLAP 서빙은 워크로드별 검증 필요

→ 목표 달성 여부 불확실
→ 별도 아키텍처 검토 필요할 수 있음 (e.g. Serverless SQL + Photon)
```

---

### 리스크 3: 탈퇴자 삭제 (GDPR)

```
1년치 84TB, 12만 건 삭제 → 48시간 이내
→ Delta Lake 삭제 성능이 도입 판단의 핵심 변수
→ 실패 시 별도 삭제 아키텍처 필요
```

---

### 리스크 4: CDC + Schema Evolution + 실시간 조회 동시 검증

```
운영 난이도 높은 조합
├── CDC 순서 보장
├── Exactly-Once
├── Schema Evolution
├── Merge 성능
├── 실시간 조회 영향
├── Small File
└── Compaction

→ 개별 검증 후 통합 검증 순서 권장
```

---

### 리스크 5: MLOps 범위

```
BM Index, LAL, Feature Store, Vector Search, Real-time Serving
→ 데이터 플랫폼 PoC와 별도 프로젝트급 규모
→ 분리 관리 권장
```

---

## 21. PoC 우선순위 권장

---

### 1순위 — 데이터 플랫폼 핵심

```
□ HDFS / Kudu / Hive / Iceberg → Delta 전환
□ Kafka → Delta Streaming
□ CDC 처리
□ 36TB 배치 파이프라인 전환
□ SQL 성능 비교 (Impala/Trino vs Databricks)
```

---

### 2순위 — 운영/보안

```
□ Unity Catalog 권한/마스킹
□ QueryPie 연동
□ Audit Log
□ SSO (Keycloak ↔ AWS SSO ↔ Databricks)
□ Service Principal
□ Workflow 승인 (샤카 연동)
```

---

### 3순위 — BI 연동

```
□ MSTR ↔ Databricks SQL Warehouse 연결
□ 큐브 쿼리 성능
□ 동시 사용자 테스트
□ Dashboard 성능
```

---

### 4순위 — TCO 최적화

```
□ Photon On/Off ROI
□ Serverless vs Classic SQL Warehouse
□ Spot Instance
□ Cluster Policy
□ S3 Lifecycle (Standard-IA, Glacier)
□ OPTIMIZE / VACUUM
```

---

### 5순위 — ML / MLOps

```
□ 기존 BM Index 모델 이관
□ Feature Store 구성
□ Batch Inference (2,000만 유저)
□ GPU 분산 학습
□ LAL 모델
□ Real-time Model Serving
```

---

## 22. 최종 요약

### 한 줄 정의

> 이 PoC는 **"Databricks가 Cloudera의 대체재가 될 수 있는가"** 를 넘어서,
> **"Databricks를 전사 데이터·AI 플랫폼으로 쓸 수 있는가"** 를 검증하는 프로젝트

---

### 5대 핵심 검증 축

| 축 | 핵심 질문 |
|:---|:---|
| 데이터 이관 가능성 | Hive/Kudu/Iceberg/HDFS를 Delta/S3로 완전히 옮길 수 있는가 |
| 성능 개선 가능성 | Impala/Trino/StarRocks 대비 Databricks SQL/Photon이 충분히 빠른가 |
| 운영 안정성 | CDC/실시간 적재/스키마 변경/탈퇴자 삭제/장애 복구가 가능한가 |
| 거버넌스/보안 | Unity Catalog/권한/마스킹/감사로그/SSO가 사내 기준을 만족하는가 |
| AI/ML 확장성 | 기존 ML 파이프라인/Feature Store/Batch·Real-time Inference까지 운영 가능한가 |

---

### AS-IS → TO-BE 전환 요약

```
AS-IS (Cloudera 온프레미스)     TO-BE (Databricks 클라우드)
────────────────────────────────────────────────────────────
HDFS                       →   S3
Hive Metastore             →   Unity Catalog
Kudu                       →   Delta Lake
Impala / Trino             →   Databricks SQL / Photon
Hive ETL                   →   Databricks Workflow / DLT
Oozie / Airflow            →   Databricks Workflow + Airflow Operator
Apache Ranger              →   Unity Catalog 권한 정책
MSTR BI                    →   Databricks SQL Warehouse 연동
온프렘 ML 파이프라인        →   Databricks MLflow + Feature Store
```
