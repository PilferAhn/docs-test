# CDF - Cloudera DataFlow (Gemini 답변)

> 출처: Gemini 답변 원문

## 4. 데이터 스트리밍 (Real-time)

실시간으로 발생하는 데이터를 처리하고 수집하는 서비스입니다.

### Cloudera DataFlow (CDF)
Apache NiFi, Kafka, Flink를 하나로 묶은 서비스입니다.

- **Apache NiFi**: GUI 기반의 No-code 데이터 수집(Ingestion) 능력이 독보적
  - 코드 없이 마우스로 데이터 흐름을 설계 가능
  - 엣지 컴퓨팅(Edge2AI) 시나리오에 강함 (IoT 센서, 공장 기기 등 현장 데이터 수집)
- **Apache Kafka**: 고성능 분산 메시지 큐
- **Apache Flink**: 실시간 스트리밍 처리 엔진

### Databricks 대응: Delta Live Tables & Spark Structured Streaming
Databricks는 스트리밍을 별도 툴보다는 **Spark의 연장선**으로 처리합니다.

- **Delta Live Tables**: 실시간 데이터를 테이블 형태로 자동 처리 (CDF의 스트리밍 분석 기능 수행)
- **Spark Structured Streaming**: Spark의 스트리밍 처리 API

### 주요 차이점
| 항목 | CDF (NiFi/Flink/Kafka) | Databricks |
|:---|:---|:---|
| No-code 수집 | ✅ NiFi (강점) | ❌ 상대적으로 약함 |
| 스트리밍 분석 | ✅ Flink | ✅ Spark Structured Streaming |
| 엣지 컴퓨팅 | ✅ NiFi Edge | ❌ 기본 미지원 |
| 메시지 큐 | ✅ Kafka 포함 | ❌ 외부 Kafka 연동 필요 |
| 선언형 스트리밍 | 제한적 | ✅ Delta Live Tables |

**단점**: NiFi 같은 GUI 기반의 범용 수집 도구 역할은 Databricks에서 상대적으로 약합니다.
