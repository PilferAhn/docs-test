import boto3
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from fnmatch import fnmatch

# ============================================================
# S3 경로 삭제 유틸리티
# ============================================================
# Databricks 환경: dbutils.fs 사용
# 순수 Python 환경: boto3 사용
#
# S3 구조 복습:
#   S3에는 진짜 "폴더"가 없다. 모든 것은 객체(파일)다.
#   "폴더처럼 보이는 것"은 키(key)에 '/'가 포함된 객체이거나
#   크기가 0인 빈 객체(폴더 마커)다.
#   → 폴더를 삭제한다 = 해당 prefix로 시작하는 모든 객체를 삭제한다
# ============================================================

s3 = boto3.client("s3")


def _parse_s3_path(s3_path: str) -> tuple[str, str]:
    """
    's3://bucket/prefix/path/' → ('bucket', 'prefix/path/')
    """
    s3_path = s3_path.replace("s3://", "").replace("s3a://", "")
    bucket, _, prefix = s3_path.partition("/")
    return bucket, prefix


def _list_all_objects(bucket: str, prefix: str) -> list[dict]:
    """
    해당 prefix 아래의 모든 객체 목록 반환 (페이지네이션 처리 포함).
    S3 list_objects는 최대 1000개만 반환하므로 paginator 필수.
    """
    paginator = s3.get_paginator("list_objects_v2")
    objects = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        objects.extend(page.get("Contents", []))
    return objects


# ============================================================
# 1. 특정 경로의 파일만 삭제 (하위 폴더 구조는 유지)
# ============================================================
# 폴더 마커(빈 객체)는 남겨두고 실제 데이터 파일만 지운다.
# 사용 예: 특정 파티션의 데이터만 비우고 폴더 구조는 보존할 때
# ============================================================
def delete_files_only(s3_path: str, dry_run: bool = False) -> int:
    bucket, prefix = _parse_s3_path(s3_path)
    objects = _list_all_objects(bucket, prefix)

    # 폴더 마커(크기 0, '/'로 끝나는 키)는 제외하고 실제 파일만 필터링
    files = [obj for obj in objects if obj["Size"] > 0]

    if not files:
        print("삭제할 파일 없음")
        return 0

    print(f"삭제 대상 파일 수: {len(files)}개")
    if dry_run:
        for f in files:
            print(f"  [DRY-RUN] {f['Key']}")
        return len(files)

    delete_keys = [{"Key": obj["Key"]} for obj in files]
    # delete_objects는 한 번에 최대 1000개 처리 가능
    for i in range(0, len(delete_keys), 1000):
        s3.delete_objects(Bucket=bucket, Delete={"Objects": delete_keys[i:i+1000]})

    print(f"파일 {len(files)}개 삭제 완료")
    return len(files)


# ============================================================
# 2. 특정 경로의 폴더(빈 폴더 마커)만 삭제
# ============================================================
# 실제 데이터 파일은 남기고 폴더 마커 객체만 제거.
# 사용 예: 빈 폴더 정리, 불필요한 폴더 마커 제거
# ============================================================
def delete_folders_only(s3_path: str, dry_run: bool = False) -> int:
    bucket, prefix = _parse_s3_path(s3_path)
    objects = _list_all_objects(bucket, prefix)

    # 폴더 마커: 크기가 0이고 키가 '/'로 끝나는 객체
    folders = [obj for obj in objects if obj["Size"] == 0 and obj["Key"].endswith("/")]

    if not folders:
        print("삭제할 폴더 마커 없음")
        return 0

    print(f"삭제 대상 폴더 마커 수: {len(folders)}개")
    if dry_run:
        for f in folders:
            print(f"  [DRY-RUN] {f['Key']}")
        return len(folders)

    delete_keys = [{"Key": obj["Key"]} for obj in folders]
    for i in range(0, len(delete_keys), 1000):
        s3.delete_objects(Bucket=bucket, Delete={"Objects": delete_keys[i:i+1000]})

    print(f"폴더 마커 {len(folders)}개 삭제 완료")
    return len(folders)


# ============================================================
# 3. 특정 경로 하위 모든 것 삭제 (폴더 + 파일 전부)
# ============================================================
# 해당 prefix로 시작하는 객체를 전부 삭제.
# 사용 예: 파티션 전체 재적재 전 초기화, 테스트 데이터 정리
# ============================================================
def delete_all(s3_path: str, dry_run: bool = False) -> int:
    bucket, prefix = _parse_s3_path(s3_path)
    objects = _list_all_objects(bucket, prefix)

    if not objects:
        print("삭제할 객체 없음")
        return 0

    print(f"삭제 대상 객체 수: {len(objects)}개")
    if dry_run:
        for obj in objects:
            print(f"  [DRY-RUN] {obj['Key']}")
        return len(objects)

    delete_keys = [{"Key": obj["Key"]} for obj in objects]
    for i in range(0, len(delete_keys), 1000):
        s3.delete_objects(Bucket=bucket, Delete={"Objects": delete_keys[i:i+1000]})

    print(f"전체 {len(objects)}개 삭제 완료")
    return len(objects)


# ============================================================
# 4. 강제 삭제 (내용 있어도 확인 없이 삭제)
# ============================================================
# delete_all과 동일하지만 객체 수와 관계없이 무조건 실행.
# 안전장치로 경로 확인 메시지 출력.
# 사용 예: 자동화 스크립트에서 조건 없이 경로 초기화
# ============================================================
def force_delete(s3_path: str) -> int:
    bucket, prefix = _parse_s3_path(s3_path)
    objects = _list_all_objects(bucket, prefix)

    if not objects:
        print("삭제할 객체 없음")
        return 0

    print(f"[FORCE DELETE] {s3_path} 하위 {len(objects)}개 객체 강제 삭제 시작")

    delete_keys = [{"Key": obj["Key"]} for obj in objects]
    deleted = 0
    for i in range(0, len(delete_keys), 1000):
        resp = s3.delete_objects(Bucket=bucket, Delete={"Objects": delete_keys[i:i+1000]})
        deleted += len(resp.get("Deleted", []))

    print(f"강제 삭제 완료: {deleted}개")
    return deleted


# ============================================================
# 5. 특정 파티션만 삭제 (날짜/키 지정)
# ============================================================
# ETL 재처리 시 특정 날짜 파티션만 골라서 삭제.
# 사용 예: dt=2024-01-01 데이터만 재적재 필요할 때
# ============================================================
def delete_partition(s3_base_path: str, partition_key: str, partition_value: str, dry_run: bool = False) -> int:
    # 예: delete_partition("s3://bucket/data/", "dt", "2024-01-01")
    #     → s3://bucket/data/dt=2024-01-01/ 삭제
    partition_path = f"{s3_base_path.rstrip('/')}/{partition_key}={partition_value}/"
    print(f"파티션 삭제 대상: {partition_path}")
    return delete_all(partition_path, dry_run=dry_run)


# ============================================================
# 6. 여러 파티션 병렬 삭제
# ============================================================
# 날짜 범위 등 여러 파티션을 동시에 삭제.
# 순차 삭제 대비 파티션 수만큼 빠름.
# 사용 예: 월 단위 재처리 시 30개 파티션 한 번에 삭제
# ============================================================
def delete_partitions_parallel(s3_base_path: str, partition_key: str, partition_values: list[str], max_workers: int = 10) -> dict:
    results = {}

    def _delete_one(value: str):
        path = f"{s3_base_path.rstrip('/')}/{partition_key}={value}/"
        count = delete_all(path)
        return value, count

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_delete_one, v): v for v in partition_values}
        for future in as_completed(futures):
            value, count = future.result()
            results[value] = count
            print(f"  완료: {partition_key}={value} → {count}개 삭제")

    total = sum(results.values())
    print(f"\n병렬 삭제 완료 | 파티션 {len(results)}개 | 총 {total}개 객체")
    return results


# ============================================================
# 7. 패턴 매칭 파일 삭제
# ============================================================
# 특정 확장자나 파일명 패턴에 맞는 파일만 삭제.
# 사용 예: _SUCCESS, .crc, _committed 같은 메타 파일 정리
# ============================================================
def delete_by_pattern(s3_path: str, pattern: str, dry_run: bool = False) -> int:
    # 예: delete_by_pattern("s3://bucket/data/", "_SUCCESS")
    #     delete_by_pattern("s3://bucket/data/", "*.crc")
    bucket, prefix = _parse_s3_path(s3_path)
    objects = _list_all_objects(bucket, prefix)

    matched = [obj for obj in objects if fnmatch(obj["Key"].split("/")[-1], pattern)]

    if not matched:
        print(f"패턴 '{pattern}'에 매칭된 파일 없음")
        return 0

    print(f"패턴 '{pattern}' 매칭 파일 수: {len(matched)}개")
    if dry_run:
        for f in matched:
            print(f"  [DRY-RUN] {f['Key']}")
        return len(matched)

    delete_keys = [{"Key": obj["Key"]} for obj in matched]
    for i in range(0, len(delete_keys), 1000):
        s3.delete_objects(Bucket=bucket, Delete={"Objects": delete_keys[i:i+1000]})

    print(f"패턴 삭제 완료: {len(matched)}개")
    return len(matched)


# ============================================================
# 8. N일 이상 지난 파일 삭제 (오래된 데이터 정리)
# ============================================================
# S3 객체의 LastModified 기준으로 오래된 파일 삭제.
# 사용 예: 임시 데이터, 로그 파일 주기적 정리 (데이터 보존 정책)
# ============================================================
def delete_older_than(s3_path: str, days: int, dry_run: bool = False) -> int:
    bucket, prefix = _parse_s3_path(s3_path)
    objects = _list_all_objects(bucket, prefix)

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    old_objects = [obj for obj in objects if obj["LastModified"] < cutoff]

    if not old_objects:
        print(f"{days}일 이상 지난 파일 없음")
        return 0

    print(f"{days}일 이상 지난 파일 수: {len(old_objects)}개 (기준: {cutoff.date()})")
    if dry_run:
        for obj in old_objects:
            age = (datetime.now(timezone.utc) - obj["LastModified"]).days
            print(f"  [DRY-RUN] {obj['Key']} (경과: {age}일)")
        return len(old_objects)

    delete_keys = [{"Key": obj["Key"]} for obj in old_objects]
    for i in range(0, len(delete_keys), 1000):
        s3.delete_objects(Bucket=bucket, Delete={"Objects": delete_keys[i:i+1000]})

    print(f"오래된 파일 {len(old_objects)}개 삭제 완료")
    return len(old_objects)


# ============================================================
# 9. 삭제 전 미리보기 (Dry-run 전용)
# ============================================================
# 실제 삭제 없이 어떤 파일이 삭제될지 목록만 출력.
# 모든 삭제 함수에 dry_run=True 옵션이 있지만
# 이 함수는 크기/날짜 요약까지 함께 보여줌.
# ============================================================
def preview_delete(s3_path: str) -> None:
    bucket, prefix = _parse_s3_path(s3_path)
    objects = _list_all_objects(bucket, prefix)

    if not objects:
        print("삭제할 객체 없음")
        return

    total_size = sum(obj["Size"] for obj in objects)
    oldest = min(objects, key=lambda x: x["LastModified"])
    newest = max(objects, key=lambda x: x["LastModified"])

    print(f"{'='*55}")
    print(f"경로        : {s3_path}")
    print(f"총 객체 수  : {len(objects)}개")
    print(f"총 용량     : {total_size / (1024**3):.2f} GB")
    print(f"가장 오래된 : {oldest['LastModified'].date()} — {oldest['Key']}")
    print(f"가장 최근   : {newest['LastModified'].date()} — {newest['Key']}")
    print(f"{'='*55}")
    print("※ 실제 삭제하려면 delete_all() 또는 force_delete() 호출")


# ============================================================
# 실행 예시
# ============================================================
if __name__ == "__main__":
    BASE = "s3://aws-s3-jimin-test/raw-data/"

    # 삭제 전 반드시 미리보기 먼저
    preview_delete(BASE)

    # 파일만 삭제 (폴더 구조 유지)
    # delete_files_only(BASE + "dt=2024-01-01/", dry_run=True)

    # 폴더 마커만 삭제
    # delete_folders_only(BASE, dry_run=True)

    # 특정 경로 전체 삭제
    # delete_all(BASE + "dt=2024-01-01/", dry_run=True)

    # 강제 전체 삭제
    # force_delete(BASE + "dt=2024-01-01/")

    # 특정 파티션 삭제
    # delete_partition(BASE, "dt", "2024-01-01", dry_run=True)

    # 여러 파티션 병렬 삭제
    # dates = [f"2024-01-{str(d).zfill(2)}" for d in range(1, 11)]
    # delete_partitions_parallel(BASE, "dt", dates, max_workers=10)

    # 패턴 매칭 삭제 (_SUCCESS, .crc 등 메타파일 정리)
    # delete_by_pattern(BASE, "_SUCCESS", dry_run=True)
    # delete_by_pattern(BASE, "*.crc", dry_run=True)

    # 30일 이상 지난 파일 삭제
    # delete_older_than(BASE, days=30, dry_run=True)
