"""
S3에 Parquet 파일이 저장될 때의 디렉토리 구조
==============================================
Spark/Databricks는 파티션 컬럼(예: dt)을 기준으로 폴더를 자동 생성하고,
각 파티션 안에 병렬 처리한 태스크 수만큼 part 파일을 나눠서 저장한다.
part 파일 하나 = Spark 태스크(파티션) 하나가 처리한 데이터 덩어리.

```mermaid
graph TD
    ROOT["s3://aws-s3-jimin-test/raw-data/"]

    ROOT --> D1["dt=2024-01-01/"]
    ROOT --> D2["dt=2024-01-02/"]
    ROOT --> D3["dt=2024-01-03/"]
    ROOT --> DX["  ...  "]

    D1 --> F1A["part-00000-a1b2c3.snappy.parquet"]
    D1 --> F1B["part-00001-d4e5f6.snappy.parquet"]
    D1 --> F1C["part-00002-g7h8i9.snappy.parquet"]

    D2 --> F2A["part-00000-j1k2l3.snappy.parquet"]
    D2 --> F2B["part-00001-m4n5o6.snappy.parquet"]

    D3 --> F3A["part-00000-p7q8r9.snappy.parquet"]

    style ROOT fill:#FF9900,color:#000,stroke:#cc7700
    style D1  fill:#1a73e8,color:#fff,stroke:#1557b0
    style D2  fill:#1a73e8,color:#fff,stroke:#1557b0
    style D3  fill:#1a73e8,color:#fff,stroke:#1557b0
    style DX  fill:#ccc,color:#555,stroke:#aaa
    style F1A fill:#34a853,color:#fff,stroke:#2d8f47
    style F1B fill:#34a853,color:#fff,stroke:#2d8f47
    style F1C fill:#34a853,color:#fff,stroke:#2d8f47
    style F2A fill:#34a853,color:#fff,stroke:#2d8f47
    style F2B fill:#34a853,color:#fff,stroke:#2d8f47
    style F3A fill:#34a853,color:#fff,stroke:#2d8f47
```

각 레이어 설명
--------------
[주황] S3 버킷 루트 경로
[파랑] 파티션 폴더 (dt=날짜) — Spark이 partitionBy("dt") 시 자동 생성
[초록] part 파일 — Spark 병렬 태스크 수만큼 분할 저장
         파일명 구조: part-{태스크번호}-{UUID}.{압축방식}.parquet
         압축 방식: snappy (기본값, 속도 우선) / gzip (용량 우선)
         파일 수 = 해당 파티션의 Spark 태스크(executor core) 수

COPY INTO는 이 구조에서 dt=날짜/ 경로를 지정하면
그 안의 모든 part 파일을 한 번에 읽어 Delta Table에 적재한다.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

S3_BASE_PATH = "s3://aws-s3-jimin-test/raw-data/"
TARGET_TABLE  = "my_database.etl_target"

# ============================================================
# 대용량 ETL에서 데이터를 가져올 때 써야 하는 방법
# ============================================================
# COPY INTO란?
#   Databricks가 제공하는 S3 → Delta Table 대용량 적재 전용 명령어.
#   일반 spark.read().write()와 다른 핵심 특징:
#     1. 멱등성(Idempotent): 이미 적재된 파일은 자동으로 건너뜀
#        → 실패 후 재실행해도 중복 적재 없음
#     2. 파일 추적: 어떤 파일을 적재했는지 Delta 메타데이터에 기록
#     3. 대용량 최적화: 수백만 개의 파일도 안정적으로 처리
#     4. 스키마 진화 지원: EVOLVE 옵션으로 컬럼 추가 자동 반영
# ============================================================


# ============================================================
# 방법 1: 순차 COPY INTO - 느린 이유
# ============================================================
# 파티션(날짜)별로 COPY INTO를 하나씩 순서대로 실행.
# 각 COPY INTO는 S3에서 파일 목록 조회 → 파일 다운로드 → Delta 기록
# 이 전체 과정이 끝나야 다음 파티션을 시작함.
#
# 타임라인: [2024-01-01 적재] → [2024-01-02 적재] → ... → [2024-01-10 적재]
#           (파티션 수가 많을수록 총 시간이 선형으로 증가)
# ============================================================
def etl_sequential(date_partitions: list[str]):
    for date in date_partitions:
        s3_path = f"{S3_BASE_PATH}dt={date}/"

        # COPY INTO가 끝날 때까지 다음 날짜로 진행 불가 (blocking)
        spark.sql(f"""
            COPY INTO {TARGET_TABLE}
            FROM '{s3_path}'
            FILEFORMAT = PARQUET
            FORMAT_OPTIONS ('mergeSchema' = 'true')
            COPY_OPTIONS ('mergeSchema' = 'true')
        """)
        print(f"Loaded: {s3_path}")


# ============================================================
# 방법 2: 병렬 COPY INTO - 대용량 ETL 권장 방식
# ============================================================
# ThreadPoolExecutor로 파티션별 COPY INTO를 동시에 실행.
#
# COPY INTO는 내부적으로 S3 API를 대량 호출하는 I/O 집약 작업이라
# 스레드 병렬화 효과가 매우 크다.
#
# 핵심 동작:
#   executor.submit()은 COPY INTO를 던지고 즉시 반환 (응답 안 기다림)
#   → 10개 파티션을 거의 동시에 던짐
#   → 각 스레드가 독립적으로 자기 파티션 적재를 완료
#
# 타임라인: [2024-01-01 적재]
#           [2024-01-02 적재]
#           [2024-01-03 적재]  → 동시에 실행
#           ...
#           [2024-01-10 적재]
#
# 총 소요 시간 ≈ 가장 오래 걸리는 단일 파티션 1개 분량
# ============================================================
def etl_parallel(date_partitions: list[str], max_workers: int = 10):

    def copy_partition(date: str):
        s3_path = f"{S3_BASE_PATH}dt={date}/"

        # 각 스레드가 독립적으로 COPY INTO 실행
        # 이미 적재된 파일은 COPY INTO가 자동으로 건너뜀 (멱등성)
        spark.sql(f"""
            COPY INTO {TARGET_TABLE}
            FROM '{s3_path}'
            FILEFORMAT = PARQUET
            FORMAT_OPTIONS ('mergeSchema' = 'true')
            COPY_OPTIONS ('mergeSchema' = 'true')
        """)
        return s3_path

    # 파티션 수만큼 스레드를 생성 (단, 과도한 스레드는 오히려 역효과)
    # max_workers는 클러스터 코어 수와 S3 rate limit을 고려해 조정
    with ThreadPoolExecutor(max_workers=max_workers) as executor:

        # 10개 파티션을 응답 기다리지 않고 연달아 던짐
        futures = {executor.submit(copy_partition, date): date for date in date_partitions}

        # 완료된 파티션부터 순서대로 결과 수거 (완료 순서 = 빠른 것 먼저)
        for future in as_completed(futures):
            try:
                print(f"Loaded: {future.result()}")
            except Exception as e:
                # 특정 파티션 실패 시 다른 파티션은 계속 진행
                # COPY INTO 멱등성 덕분에 실패한 파티션만 재실행하면 됨
                failed_date = futures[future]
                print(f"Failed: dt={failed_date} → {e}")


# ============================================================
# 실행 예시
# ============================================================
if __name__ == "__main__":
    date_partitions = [f"2024-01-{str(d).zfill(2)}" for d in range(1, 11)]

    # 방법 1: 순차 (비권장 - 파티션 수만큼 시간 선형 증가)
    # etl_sequential(date_partitions)

    # 방법 2: 병렬 (권장 - 파티션이 많아도 시간이 거의 일정)
    etl_parallel(date_partitions, max_workers=10)


# ============================================================
# 언제 max_workers를 조정해야 하는가?
# ============================================================
# max_workers=10  → 일반적인 경우, 파티션 수와 맞추는 게 기본
# max_workers=5   → S3 요청이 너무 많아 ThrottlingException 발생 시 줄임
# max_workers=20+ → 파티션이 수백 개이고 클러스터 자원이 충분할 때 늘림
#
# ※ COPY INTO vs Auto Loader 선택 기준
#   COPY INTO  : 과거 데이터 백필(Backfill), 특정 파티션 재적재, 1회성 배치
#   Auto Loader: 신규 파일이 S3에 계속 쌓이는 스트리밍/준실시간 파이프라인
# ============================================================
