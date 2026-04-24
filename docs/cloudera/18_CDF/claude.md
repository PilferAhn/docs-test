# CDF - Cloudera DataFlow (Claude 정리)

> GPT 답변 + Gemini 답변을 종합 정리한 버전
> (이 서비스는 Gemini 답변이 주된 출처입니다. GPT는 하둡 컴포넌트 수준에서 비교했기 때문에 CDF를 직접 다루지 않았습니다.)

## CDF란?

**실시간으로 발생하는 데이터를 수집, 이동, 처리하는 스트리밍 데이터 서비스**입니다.

> **스트리밍이란?** 공장 센서, 앱 로그, 금융 거래 등 **쉬지 않고 쏟아지는 데이터**를 즉시 처리하는 것입니다.

## Cloudera에서의 역할

CDF = Apache NiFi + Apache Kafka + Apache Flink의 통합 서비스

| 구성 요소 | 역할 | 특징 |
|:---|:---|:---|
| **Apache NiFi** | 데이터 수집 | GUI 기반 No-code 설계, IoT·엣지 강점 |
| **Apache Kafka** | 메시지 큐 | 고성능 분산 메시지 스트리밍 |
| **Apache Flink** | 스트리밍 처리 | 실시간 데이터 변환·분석 |

CDF의 최대 강점: **NiFi의 GUI 기반 No-code 수집 기능**
코드를 모르는 운영자도 마우스로 데이터 파이프라인을 그릴 수 있습니다.

## Databricks 대응

Gemini의 핵심 지적: Databricks는 스트리밍을 별도 도구가 아닌 **Spark의 연장선**으로 처리합니다.

| CDF 기능 | Databricks 대응 |
|:---|:---|
| NiFi (No-code 수집) | ❌ 직접 대응 없음 (외부 도구 필요) |
| Kafka (메시지 큐) | ❌ 외부 Kafka 연동 (AWS MSK, Azure Event Hub 등) |
| Flink (스트리밍 분석) | **Spark Structured Streaming** |
| 선언형 스트리밍 파이프라인 | **Delta Live Tables** |
| 엣지 컴퓨팅 | ❌ 기본 미지원 |

### 전환 시 주의점
CDF에서 Databricks로 전환할 때 가장 큰 차이점:
- **NiFi 대체재가 없음**: GUI 기반 No-code 수집 도구를 별도로 선택해야 함
  (예: Apache NiFi 독립 운영, AWS Glue, Azure Data Factory 등)
- **Kafka는 외부 서비스 연동**: Databricks는 Kafka를 직접 포함하지 않음

## 한 줄 요약

**CDF ≈ Spark Structured Streaming + Delta Live Tables**
(NiFi의 No-code 수집 기능은 직접 대응 없음 — 가장 큰 전환 과제)
