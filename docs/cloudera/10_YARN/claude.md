# YARN (Claude 정리)

> GPT 답변 + Gemini 답변을 종합 정리한 버전

## YARN이란?

Hadoop의 **리소스 관리 및 스케줄링 계층**입니다.

HDFS가 "저장 계층"이라면, YARN은 **CPU·메모리 자원을 어떻게 배분할지 결정하는 계층**입니다.

Spark, Tez, MapReduce 같은 실행 엔진들이 "CPU 몇 개, 메모리 몇 GB 줘"라고 YARN에게 요청하면,
YARN이 클러스터 전체의 가용 자원을 파악하고 요청들을 스케줄링합니다.

## Cloudera에서의 역할

GPT 관점:
- 클러스터 전체 자원 스케줄링
- 애플리케이션별 컨테이너(CPU+메모리 단위) 할당
- 여러 팀이 자원을 나눠 쓰는 멀티테넌시 지원
- 운영자가 직접 YARN 자원 모델을 관리해야 함

Gemini 추가 관점:
- CDE에서는 YARN 대신 **Kubernetes**가 자원 관리 역할을 함
- 즉, Hadoop 생태계 내에서도 YARN → Kubernetes 전환 흐름 존재

## Databricks 대응

GPT와 Gemini 모두 동일하게, **YARN에 대응하는 사용자 노출 서비스가 없습니다.**
Databricks의 컨트롤 플레인과 클라우드 VM 오케스트레이션 내부로 완전히 흡수됩니다.

| 항목 | YARN | Databricks |
|:---|:---|:---|
| 자원 단위 | 컨테이너(Container) | Cluster / SQL Warehouse / Serverless |
| 사용자 관리 | 직접 큐 설정, 자원 배분 조정 | Cluster 크기 선택만 하면 됨 |
| 스케줄링 | YARN 스케줄러 직접 관리 | 플랫폼이 자동 처리 |
| 현대화 경로 | YARN → Kubernetes | Serverless compute |

## 한 줄 요약

**YARN ≈ Databricks 내부 Compute/Resource 관리 플레인**
(사용자에게 노출되는 독립 서비스 없음, 플랫폼이 자동 처리)
