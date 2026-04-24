# Kudu (Claude 정리)

> GPT 답변 + Gemini 답변을 종합 정리한 버전

## Kudu란?

Hadoop 플랫폼용 **컬럼형(Columnar) 분산 저장 엔진**입니다.

일반 파일 저장(HDFS)과 달리, **분석에 특화된 저장 방식**으로 빠른 읽기와 일부 업데이트(UPSERT)를 지원합니다.
Impala와 조합해 저지연 분석에 자주 사용됩니다.

## Cloudera에서의 역할

| 특징 | 설명 |
|:---|:---|
| 저장 방식 | 컬럼형(Column-oriented) → 분석 쿼리에 최적화 |
| 업데이트 | UPSERT(없으면 Insert, 있으면 Update) 지원 |
| 조합 | Impala + Kudu → 저지연 분석 |
| 성격 | "파일 시스템"이 아닌 "분산 저장 엔진" |

## Databricks 대응

GPT는 **Delta Lake**를 가장 가까운 대응으로 지목합니다.
Gemini는 Kudu를 독립적으로 다루지 않았지만, Databricks SQL의 기반 저장 계층으로 Delta Lake를 설명합니다.

| 항목 | Kudu | Delta Lake |
|:---|:---|:---|
| 저장 위치 | 자체 분산 스토리지 엔진 | 클라우드 오브젝트 스토리지(S3/ADLS/GCS) 위 |
| 파일 포맷 | 자체 포맷 | Parquet + 트랜잭션 로그 |
| ACID 트랜잭션 | 지원 | 지원 |
| UPSERT/Merge | 지원 | 지원 (MERGE INTO 구문) |
| 스트리밍 통합 | 가능 | 매우 강력 (Structured Streaming) |
| 완전 동일? | ❌ 설계 철학 다름 | 가장 가까운 대응 |

## 한 줄 요약

**Kudu ≈ Delta Lake**
(특히 UPSERT/Merge 가능한 분석용 테이블 계층으로 이해)
