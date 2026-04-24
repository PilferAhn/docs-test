# Kudu (Gemini 답변)

> 출처: Gemini 답변 원문
> Gemini는 Kudu를 개별 컴포넌트로 별도 다루지 않았습니다.
> CDW(데이터 웨어하우징) 맥락에서 간접적으로 관련됩니다.

## Gemini의 관련 언급

Gemini 답변에서 Kudu는 명시적으로 언급되지 않았으나,
CDW에서 Impala와 조합해 사용하는 저장 엔진으로 관련됩니다.

### 간접 관련 내용 (CDW 맥락)
Cloudera Data Warehouse(CDW)는 Impala 엔진을 통해 HDFS/Kudu 기반 데이터를 분석합니다.
Databricks에서는 이 역할을 Delta Lake 테이블이 대체합니다.

Delta Lake의 특징 (Gemini가 설명한 Databricks SQL의 기반):
- 오픈소스 테이블 포맷
- ACID 트랜잭션 지원
- 스트리밍과 배치 통합
- Photon 엔진과 함께 사용

## Gemini 관점 요약

Kudu는 Gemini 답변에서 독립 서비스로 비교되지 않았습니다.
상세 비교는 GPT 답변(`gpt.md`) 또는 Claude 정리(`claude.md`)를 참고하세요.
