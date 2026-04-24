# Kudu (GPT 답변)

> 출처: ChatGPT 답변 원문

## Cloudera에서의 역할

Kudu는 **Hadoop 플랫폼용 columnar storage manager**입니다.
확장성과 고가용성을 갖고, OLAP 워크로드 처리와 Spark/MapReduce/Flume 등과 통합됩니다.
Impala와 함께 자주 쓰이며, HDFS처럼 단순 파일 저장만 하는 것이 아니라 **더 빠른 랜덤 읽기/갱신 성향**을 노리는 저장 엔진입니다.

### 실제 역할 상세
- 빠른 분석용 컬럼형 저장
- 일부 업데이트/UPSERT 패턴에 유리
- Impala와 조합해 저지연 분석
- HDFS보다 "파일 시스템"보다는 "분산 저장 엔진" 성격이 강함

## Databricks 대응

가장 가까운 대응은 **Delta Lake 테이블**입니다.

Delta Lake는 Parquet 파일에 트랜잭션 로그를 더해 ACID와 확장 가능한 메타데이터 처리를 제공하고, Databricks 테이블의 기반 저장 계층입니다.

Kudu가 "분석 친화적 저장 엔진 + 일부 업데이트 친화성"을 노렸다면, Databricks에서는 그 역할을 **Delta Lake**가 맡습니다.

### 단, 완전히 같지는 않음
- Kudu: 별도 분산 스토리지 엔진
- Delta Lake: 클라우드 오브젝트 스토리지 위에 놓이는 테이블 포맷/저장 계층
- 설계 철학이 다르지만, "분석용 운영 테이블 저장 계층"으로 비교하면 가장 가깝습니다.

## 한 줄 매핑

**Kudu ≈ Delta Lake**
특히 upsert/merge 가능한 분석용 테이블 계층이라는 관점에서 보시면 됩니다.
