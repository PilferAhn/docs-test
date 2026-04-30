from pyspark.sql import SparkSession, DataFrame

spark = SparkSession.builder.getOrCreate()

# ============================================================
# S3 Parquet 적재 유틸리티
# ============================================================
# Databricks Serverless 클러스터 환경에서 발생하는 설정 이슈와
# 올바른 write 패턴을 정리한 파일.
#
# ※ Serverless vs Classic 클러스터 핵심 차이
#   Classic : spark.conf.set()으로 거의 모든 config 변경 가능
#   Serverless: 보안/격리 정책상 허용된 config만 변경 가능
#              → spark.conf.set() 대신 .option()을 써야 하는 경우가 많음
# ============================================================


# ============================================================
# [ERROR] spark.conf.set 방식 - Serverless에서 동작 안 함
# ============================================================
# 에러 메시지:
#   [CONFIG_NOT_AVAILABLE] Configuration spark.sql.files.maxRecordsPerFile
#   is not available. SQLSTATE: 42K0I
#
# 원인:
#   Serverless 클러스터는 내부적으로 공유 인프라 위에서 동작하기 때문에
#   클러스터 전역 설정(spark.conf.set)을 임의로 변경하는 것을 제한함.
#   spark.sql.files.maxRecordsPerFile은 그 제한 목록에 포함된 항목.
#
# ❌ 사용 금지 (Serverless 환경)
# spark.conf.set("spark.sql.files.maxRecordsPerFile", 10)
# ============================================================


# ============================================================
# 기본 적재 함수
# ============================================================
# partitionBy("collect_date"): 날짜 컬럼 기준으로 폴더 자동 생성
#   → s3://.../table_name/collect_date=2024-01-01/part-xxxx.parquet
#
# maxRecordsPerFile: 파일 1개에 담을 최대 행 수 제한
#   → 대용량 데이터를 균등하게 쪼갤 때 사용
#   → spark.conf.set() 대신 .option()으로 지정해야 Serverless에서 동작
#
# mode("overwrite"): 해당 경로에 기존 데이터가 있으면 전부 덮어씀
#   → 재적재(backfill) 시 사용
#   → 주의: 경로 전체를 덮어쓰므로 partitionBy와 함께 쓸 때는
#           특정 파티션만 덮어쓰려면 아래 ingest_partition() 사용
# ============================================================
def ingest_basic(df: DataFrame, table_name: str, max_records: int = 50) -> None:
    s3_path = f"s3://aws-s3-jimin-test/test/{table_name}/"

    df.write \
        .partitionBy("collect_date") \
        .option("maxRecordsPerFile", max_records) \
        .mode("overwrite") \
        .parquet(s3_path)

    print(f"저장 완료: {s3_path}")


# ============================================================
# 특정 파티션만 덮어쓰는 적재 함수
# ============================================================
# mode("overwrite") 단독 사용 시 문제점:
#   partitionBy를 써도 경로 전체(모든 날짜)를 삭제하고 다시 씀
#   → 2024-01-01 데이터만 재적재하려다가 전체 날짜 날아가는 사고 발생
#
# 해결: partitionOverwriteMode = "dynamic" 설정
#   → df에 포함된 collect_date 값의 파티션 폴더만 덮어씀
#   → 나머지 날짜 파티션은 건드리지 않음
#
# ✅ 부분 재처리, 특정 날짜 재적재 시 반드시 이 방식 사용
# ============================================================
def ingest_partition(df: DataFrame, table_name: str, max_records: int = 50) -> None:
    s3_path = f"s3://aws-s3-jimin-test/test/{table_name}/"

    # dynamic: df에 있는 파티션만 덮어씀 (static은 전체 덮어씀)
    spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

    df.write \
        .partitionBy("collect_date") \
        .option("maxRecordsPerFile", max_records) \
        .mode("overwrite") \
        .parquet(s3_path)

    print(f"파티션 적재 완료: {s3_path}")


# ============================================================
# 신규 데이터만 추가 적재 (append)
# ============================================================
# mode("append"): 기존 데이터를 유지하고 새 파일만 추가
#   → 매일 증분 데이터를 쌓을 때 사용
#   → 주의: 동일 데이터를 두 번 실행하면 중복 발생
#           중복 방지가 필요하면 COPY INTO 또는 MERGE 사용
# ============================================================
def ingest_append(df: DataFrame, table_name: str, max_records: int = 50) -> None:
    s3_path = f"s3://aws-s3-jimin-test/test/{table_name}/"

    df.write \
        .partitionBy("collect_date") \
        .option("maxRecordsPerFile", max_records) \
        .mode("append") \
        .parquet(s3_path)

    print(f"증분 적재 완료: {s3_path}")


# ============================================================
# 스키마 포함 적재 (컬럼 타입 보존)
# ============================================================
# Parquet은 스키마를 파일 안에 포함하지만
# 나중에 Spark이 읽을 때 파티션별 스키마가 달라지는 경우 오류 발생.
# mergeSchema = true: 파티션마다 스키마가 조금씩 달라도 자동으로 병합
#   → 컬럼이 추가된 경우 새 컬럼은 null로 채워짐
#   → 운영 초기 스키마가 자주 바뀔 때 유용
# ============================================================
def ingest_with_schema_merge(df: DataFrame, table_name: str, max_records: int = 50) -> None:
    s3_path = f"s3://aws-s3-jimin-test/test/{table_name}/"

    spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

    df.write \
        .partitionBy("collect_date") \
        .option("maxRecordsPerFile", max_records) \
        .option("mergeSchema", "true") \
        .mode("overwrite") \
        .parquet(s3_path)

    print(f"스키마 병합 적재 완료: {s3_path}")


# ============================================================
# maxRecordsPerFile 계산 가이드
# ============================================================
# 적재 후 part 파일 1개 크기가 128MB ~ 512MB 가 되도록 조정하는 것이 목표.
# 행 수 기준으로 계산하는 방법:
#
#   전체 데이터 크기 / 원하는 파일 수 = 파일당 행 수
#   예) 1000만 행, 파일 20개 원할 때 → maxRecordsPerFile = 500,000
#
# 테스트 중에는 10~50 정도로 낮게 설정해서 파일 분할 확인 후
# 운영 전에 실제 데이터 크기 기반으로 조정할 것.
# ============================================================
def calculate_max_records(df: DataFrame, target_file_count: int) -> int:
    total_rows = df.count()
    max_records = max(1, total_rows // target_file_count)
    print(f"총 행 수: {total_rows:,} | 목표 파일 수: {target_file_count} | maxRecordsPerFile: {max_records:,}")
    return max_records


# ============================================================
# S3 파티션 병렬 이동 (ThreadPoolExecutor 버전)
# ============================================================
# 기존 for loop 방식: 파티션을 하나씩 순차로 cp + rm → 느림
# v2 방식: ThreadPoolExecutor로 10개 동시에 cp + rm → 5~10배 빠름
#
# 왜 ThreadPoolExecutor가 여기서 효과적인가?
#   - dbutils.fs.cp/rm은 드라이버에서 S3 API를 호출하는 I/O 작업
#   - 대부분의 시간이 S3 응답 대기 (네트워크 I/O)
#   - 스레드 10개면 10개 파티션을 동시에 대기 → 총 시간 1/10
#
# ※ df.write.parquet()는 이미 Spark가 분산 병렬 처리하므로
#   ThreadPoolExecutor로 감싸도 효과 없음. 여기서는 dbutils 전용!
# ============================================================
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


def move_partitions_parallel(
    table_name: str,
    cutoff_date: str = "2025-10-01",
    max_workers: int = 10,
) -> None:
    """
    raw_data → raw_data_new2 로 cutoff_date 이후 파티션을 병렬 이동

    Args:
        table_name: 테이블명 (S3 경로에 사용)
        cutoff_date: 이 날짜 이후 파티션을 이동 (기본: 2025-10-01)
        max_workers: 동시 실행 스레드 수 (기본: 10, S3 쓰로틀링 고려)
    """
    source_base = f"s3://aws-s3-jimin-test/test/{table_name}"
    dest_base = "s3://aws-s3-jimin-test/test/raw_data_new2"

    # 파티션 폴더 목록 조회
    partitions = dbutils.fs.ls(f"{source_base}/")

    # collect_date >= cutoff_date 필터
    move_targets = [
        p for p in partitions
        if p.name.startswith("collect_date=")
        and p.name.replace("collect_date=", "").rstrip("/") >= cutoff_date
    ]

    total = len(move_targets)
    if total == 0:
        print(f"이동 대상 없음 (cutoff: {cutoff_date})")
        return

    print(f"이동 대상: {total}개 파티션 (>= {cutoff_date})")
    print(f"병렬 스레드: {max_workers}개")
    print("=" * 60)

    # --- 단일 파티션 이동 함수 ---
    # 각 스레드가 자기 인자(p)를 받아서 독립적으로 실행
    def move_one(p):
        folder_name = p.name.rstrip("/")  # e.g. "collect_date=2025-10-01"
        src = f"{source_base}/{folder_name}"
        dst = f"{dest_base}/{folder_name}"
        dbutils.fs.cp(src, dst, recurse=True)
        dbutils.fs.rm(src, recurse=True)
        return folder_name

    # --- 병렬 실행 ---
    job_start = datetime.now()
    success_count = 0
    error_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # submit: 각 파티션을 스레드에 배정
        # {Future객체: 원본파티션} 매핑 → 에러 시 어떤 파티션인지 추적용
        futures = {executor.submit(move_one, p): p for p in move_targets}

        # as_completed: 완료된 것부터 순서 상관없이 처리
        for i, future in enumerate(as_completed(futures), 1):
            try:
                folder_name = future.result()
                success_count += 1
                print(f"[{i:>3}/{total}] {folder_name} → raw_data_new2/  ✅")
            except Exception as exc:
                error_count += 1
                p = futures[future]
                print(f"[{i:>3}/{total}] {p.name} ❌ 에러: {exc}")

    # --- 결과 요약 ---
    elapsed = (datetime.now() - job_start).total_seconds()
    print("=" * 60)
    print(f"전체 완료: {elapsed:.1f}초")
    print(f"  성공: {success_count}건 | 실패: {error_count}건")
    print(f"  원본: {source_base}/")
    print(f"  이동: {dest_base}/")


# ============================================================
# 실행 예시
# ============================================================
if __name__ == "__main__":
    table_name = "sensor_log"

    # 예시 DataFrame (실제 사용 시 교체)
    df = spark.createDataFrame([
        ("2024-01-01", "A001", 98.5),
        ("2024-01-01", "A002", 97.2),
        ("2024-01-02", "A001", 96.8),
    ], ["collect_date", "equipment_id", "value"])

    # 1. 기본 적재 (전체 overwrite)
    # ingest_basic(df, table_name, max_records=50)

    # 2. 특정 파티션만 덮어쓰기 (안전한 재적재)
    # ingest_partition(df, table_name, max_records=50)

    # 3. 증분 적재 (기존 데이터 유지)
    # ingest_append(df, table_name, max_records=50)

    # 4. 스키마 변경 가능성 있을 때
    # ingest_with_schema_merge(df, table_name, max_records=50)

    # 5. maxRecordsPerFile 값 계산
    # max_records = calculate_max_records(df, target_file_count=10)
    # ingest_partition(df, table_name, max_records=max_records)

    # 6. 파티션 병렬 이동 (ThreadPoolExecutor v2)
    # move_partitions_parallel(table_name, cutoff_date="2025-10-01", max_workers=10)
