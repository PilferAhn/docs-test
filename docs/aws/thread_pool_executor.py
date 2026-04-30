# ============================================================
# Python 병렬 처리 완전 가이드
# ============================================================
# 두 가지 병렬 처리 방식을 다룸:
#   1. ThreadPoolExecutor — 드라이버 단독 I/O 작업 병렬화
#   2. Spark repartition   — 분산 클러스터 병렬 쓰기
#
# 핵심 구분:
#   - dbutils.fs.cp/rm 같은 드라이버 작업 → ThreadPoolExecutor
#   - df.write 같은 Spark 작업 → repartition (이미 분산 병렬)
# ============================================================


# ############################################################
# PART 1: Spark 병렬 쓰기와 Shuffle
# ############################################################

# ============================================================
# 1-1. df.write 는 이미 병렬이다
# ============================================================
# Spark의 df.write.parquet()는 클러스터의 모든 워커 노드에서
# 동시에 파일을 쓴다. 병렬도 = DataFrame의 파티션 수
#
# 예: 파티션 10개 → 10개 task가 동시에 S3에 parquet 작성
#     파티션 1개  → 1개 task만 순차 작성 (느림!)
#
# 파일명으로 확인 가능:
#   part-00000-...parquet  ← task 0
#   part-00001-...parquet  ← task 1
#   part-00002-...parquet  ← task 2
#
# part-00000만 존재하면 → 파티션 1개로만 쓴 것!
# (c000, c001, c002는 maxRecordsPerFile로 쪼갠 것일 뿐, 병렬 아님)


# ============================================================
# 1-2. 파티션 수가 결정되는 흐름
# ============================================================
# | 단계                        | 파티션 수 결정 방식                    |
# |----------------------------|--------------------------------------|
# | spark.read.parquet()       | 파일 수/크기 기반 자동 설정              |
# | spark.sql("SELECT ...")    | spark.sql.shuffle.partitions (기본 200)|
# | df.filter()                | 원본 파티션 수 유지                    |
# | df.groupBy().agg()         | shuffle 발생 → 200개                  |
# | df.coalesce(1)             | 강제 1개                              |
# | df.repartition(N)          | 강제 N개 (shuffle 발생)               |
#
# 파티션이 1개가 되는 흔한 원인:
#   - 데이터가 작아서 Spark가 자동으로 1개로 줄임
#   - 어딘가에서 coalesce(1) 했을 때
#   - AQE(Adaptive Query Execution)가 파티션을 합쳐버림


# ============================================================
# 1-3. Shuffle이란?
# ============================================================
# Shuffle = 데이터를 파티션 간에 재분배하는 연산
# 네트워크를 통해 워커 노드 간 데이터 이동이 발생 → 비용 큼
#
# Shuffle이 발생하는 연산:
#   - repartition(N)    : 무조건 전체 shuffle
#   - groupBy().agg()   : 같은 key끼리 모으기 위해 shuffle
#   - join()            : 양쪽 테이블을 key 기준으로 재분배
#   - orderBy()         : 전체 정렬을 위해 shuffle
#   - distinct()        : 중복 제거를 위해 shuffle
#
# Shuffle이 발생하지 않는 연산:
#   - filter()          : 각 파티션 내에서 독립 처리
#   - select()          : 컬럼 선택만
#   - coalesce(N)       : 파티션 합치기 (줄이기만, 데이터 이동 최소)
#   - map/withColumn    : 각 행 독립 변환
#
# ┌──────────────────────────────────────────────────────┐
# │           Shuffle 과정 (repartition 예시)              │
# │                                                      │
# │  [Worker 1]          [Worker 2]          [Worker 3]  │
# │  Partition 0  ─────→  Partition 0'                   │
# │  Partition 1  ─────→  Partition 1'                   │
# │               ─────→  Partition 2'                   │
# │                                                      │
# │  전체 데이터가 네트워크를 통해 재분배됨                    │
# │  = 디스크 I/O + 네트워크 I/O + 직렬화/역직렬화 비용       │
# └──────────────────────────────────────────────────────┘


# ============================================================
# 1-4. repartition vs coalesce
# ============================================================
# | 연산           | 방향      | Shuffle | 용도                       |
# |---------------|----------|---------|---------------------------|
# | repartition(N)| 늘리기/줄이기| O (항상) | 파티션 수를 N으로 균등 재분배   |
# | coalesce(N)   | 줄이기만   | X       | 파티션 합치기 (데이터 이동 최소)|
#
# repartition(10):
#   - 파티션을 1 → 10개로 늘릴 수 있음 (균등 분배)
#   - shuffle 비용 발생하지만, 쓰기 병렬도 증가
#
# coalesce(1):
#   - 파티션을 10 → 1개로 줄임
#   - shuffle 없음 (하나의 task로 합치기만)
#   - 단, 하나의 task에 모든 데이터 몰림 → 메모리 부족 위험
#
# 실무 선택 기준:
#   파티션 늘리기 → repartition (shuffle 불가피)
#   파티션 줄이기 → coalesce (shuffle 없이 가능)


# ============================================================
# 1-5. 적정 파티션 수 가이드
# ============================================================
# 목표: 파티션당 128MB ~ 256MB
#
# 공식: 적정 파티션 수 = 전체 데이터 크기 / 128MB
#
# | 데이터 크기 | 권장 파티션 수 | 이유                          |
# |-----------|-------------|------------------------------|
# | 100MB     | 1~2         | 작은 데이터, 오버헤드 최소화       |
# | 1GB       | 4~8         | 적절한 병렬도                   |
# | 10GB      | 40~80       | 충분한 병렬 + 적정 파일 크기       |
# | 100GB     | 400~800     | 대규모 병렬 처리                 |
#
# 파티션이 너무 많으면:
#   - Small file 문제 (읽기 시 오버헤드)
#   - 스케줄러 부하
#   - S3 listing 느려짐
#
# 파티션이 너무 적으면:
#   - 쓰기 느림 (병렬도 부족)
#   - 메모리 부족 (한 task에 데이터 집중)
#   - 클러스터 활용도 저하


# ============================================================
# 1-6. 실전 예시: repartition으로 쓰기 병렬화
# ============================================================

# --- BEFORE: 파티션 1개로 느리게 쓰기 ---
# df.write \
#     .partitionBy("collect_date") \
#     .option("maxRecordsPerFile", 1000) \
#     .mode("overwrite") \
#     .parquet(s3_path)
# 결과: part-00000-...c000, c001, c002 (1개 task가 순차 작성)

# --- AFTER: 병렬 쓰기 ---
# df.repartition(10) \
#     .write \
#     .partitionBy("collect_date") \
#     .option("maxRecordsPerFile", 1000) \
#     .mode("overwrite") \
#     .parquet(s3_path)
# 결과: part-00000 ~ part-00009 (10개 task 동시 작성)

# 주의: repartition + partitionBy 조합 시
#   repartition(10, "collect_date") 처럼 컬럼 지정하면
#   같은 collect_date 값이 같은 파티션으로 감 → 더 효율적
#   (불필요한 cross-partition 쓰기 방지)


# ============================================================
# 1-7. ThreadPoolExecutor로 df.write를 감싸면?
# ============================================================
# ❌ 효과 없음!
#
# df.write.parquet()는 Spark 엔진이 내부적으로 분산 처리.
# 드라이버에서 ThreadPool로 감싸도 .write 호출 자체는 1번이고,
# 실제 쓰기는 Spark executor(워커)에서 일어남.
#
# ThreadPoolExecutor가 효과 있는 경우:
#   ✅ dbutils.fs.cp 100번 호출 (드라이버 순차 실행 → 병렬화)
#   ✅ REST API 100개 호출 (I/O 대기 → 병렬화)
#   ✅ requests.get 여러 번 (네트워크 I/O → 병렬화)
#
# ThreadPoolExecutor가 효과 없는 경우:
#   ❌ df.write.parquet() (이미 Spark 분산 처리)
#   ❌ spark.sql("COPY INTO ...") (이미 Spark 분산 처리)
#   ❌ df.count() (Spark action, 이미 병렬)


# ############################################################
# PART 2: ThreadPoolExecutor 공식 문서
# ############################################################

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
    wait,
    FIRST_COMPLETED,
    FIRST_EXCEPTION,
    ALL_COMPLETED,
)
from datetime import datetime


# ============================================================
# 2-1. 클래스 시그니처
# ============================================================
# concurrent.futures.ThreadPoolExecutor(
#     max_workers=None,          # 최대 스레드 수
#                                # None이면 min(32, os.cpu_count() + 4)
#     thread_name_prefix='',     # 스레드 이름 접두사 (디버깅용)
#     initializer=None,          # 각 워커 스레드 시작 시 호출할 함수
#     initargs=()                # initializer에 전달할 인자
# )
#
# 모듈: concurrent.futures (표준 라이브러리, 설치 불필요)
# 용도: I/O 바운드 작업의 병렬 처리 (HTTP, S3, DB, 파일 I/O)
# 주의: CPU 바운드 작업은 GIL 때문에 효과 없음 → ProcessPoolExecutor 사용


# ============================================================
# 2-2. 핵심 메서드
# ============================================================

# --- submit(fn, *args, **kwargs) → Future ---
# 단일 작업 제출, Future 객체 반환
# - 가장 유연한 방식
# - Future 객체로 결과/예외를 개별 제어 가능
# future = executor.submit(fn, arg1, arg2)

# --- map(fn, *iterables, timeout=None) → Iterator ---
# 여러 작업 일괄 제출, 결과 순서 보장
# - 입력 순서대로 결과 반환 (완료 순서 아님!)
# - 중간에 예외 발생 시 이후 결과 접근 불가
# results = executor.map(fn, items, timeout=60)

# --- shutdown(wait=True, cancel_futures=False) ---
# Executor 종료
# - with문 사용 시 자동 호출됨 (권장)
# - cancel_futures=True: 대기 중인 작업 취소 (Python 3.9+)


# ============================================================
# 2-3. Future 객체 메서드
# ============================================================
# future.result(timeout=None)    # 결과 반환 (예외 시 re-raise)
# future.exception(timeout=None) # 예외 반환 (없으면 None)
# future.done()                  # 완료 여부 (bool), non-blocking
# future.cancelled()             # 취소 여부 (bool)
# future.cancel()                # 취소 시도 (실행 전에만 가능)
# future.running()               # 실행 중 여부
# future.add_done_callback(fn)   # 완료 시 콜백 등록


# ============================================================
# 2-4. 모듈 함수
# ============================================================

# --- as_completed(futures, timeout=None) → Iterator[Future] ---
# 완료된 순서대로 Future를 yield (빠른 것부터!)
# 결과를 빨리 처리하고 싶을 때 사용
#
# for future in as_completed(futures):
#     result = future.result()

# --- wait(futures, timeout=None, return_when=ALL_COMPLETED) ---
# (done, not_done) 집합 반환
# return_when 옵션:
#   FIRST_COMPLETED  — 아무거나 하나 완료되면 반환
#   FIRST_EXCEPTION  — 첫 예외 발생 시 반환
#   ALL_COMPLETED    — 전부 완료되면 반환 (기본값)
#
# done, not_done = wait(futures, return_when=FIRST_COMPLETED)


# ============================================================
# 2-5. max_workers 가이드
# ============================================================
# | 작업 유형           | 권장 max_workers       | 이유                    |
# |--------------------|-----------------------|------------------------|
# | S3/HTTP I/O        | 10~50                 | 대부분 대기 시간이라 많아도 OK  |
# | DB 쿼리            | 커넥션 풀 크기와 동일     | 풀 초과 시 의미 없음         |
# | 파일 I/O           | 5~20                  | 디스크 처리량 한계           |
# | CPU 바운드          | 1 (사용하지 말 것)       | GIL 때문에 효과 없음         |
# | Databricks dbutils | 10~20                 | S3 API 쓰로틀링 고려       |
#
# 벤치마크로 최적값 찾기:
# import time
# for workers in [5, 10, 20, 50]:
#     start = time.perf_counter()
#     with ThreadPoolExecutor(max_workers=workers) as e:
#         list(e.map(task, items))
#     print(f"{workers} workers: {time.perf_counter() - start:.2f}s")


# ============================================================
# 2-6. submit() vs map() 선택 가이드
# ============================================================
# submit() 사용:
#   - 개별 에러 핸들링 필요
#   - 완료 순서대로 처리하고 싶을 때 (as_completed)
#   - 작업마다 다른 함수/인자 조합
#   - 개별 취소가 필요할 때
#
# map() 사용:
#   - 같은 함수에 다른 인자만 넘길 때
#   - 입력 순서대로 결과가 필요할 때
#   - 간단하게 한 줄로 처리하고 싶을 때


# ############################################################
# PART 3: 실전 예시
# ############################################################

# ============================================================
# 3-1. S3 파티션 병렬 이동 (Databricks)
# ============================================================
def example_s3_parallel_move():
    """
    dbutils.fs.cp + rm 을 병렬로 수행하는 패턴
    기존 for loop 대비 5~10배 빠름
    """
    source_base = "s3://aws-s3-jimin-test/test/raw_data"
    dest_base = "s3://aws-s3-jimin-test/test/raw_data_new"
    cutoff_date = "2025-10-01"

    # 파티션 목록 조회
    partitions = dbutils.fs.ls(f"{source_base}/")
    move_targets = [
        p for p in partitions
        if p.name.startswith("collect_date=")
        and p.name.replace("collect_date=", "").rstrip("/") >= cutoff_date
    ]

    total = len(move_targets)
    print(f"이동 대상: {total}개 파티션")

    # --- 병렬 이동 ---
    def move_partition(p):
        """단일 파티션 이동 (복사 + 삭제)"""
        folder_name = p.name.rstrip("/")
        src = f"{source_base}/{folder_name}"
        dst = f"{dest_base}/{folder_name}"
        dbutils.fs.cp(src, dst, recurse=True)
        dbutils.fs.rm(src, recurse=True)
        return folder_name

    job_start = datetime.now()

    with ThreadPoolExecutor(max_workers=10) as executor:
        # submit으로 제출 → Future 딕셔너리
        future_to_partition = {
            executor.submit(move_partition, p): p
            for p in move_targets
        }

        # as_completed로 완료된 것부터 출력
        for i, future in enumerate(as_completed(future_to_partition), 1):
            try:
                folder_name = future.result()
                print(f"[{i:>3}/{total}] {folder_name} → raw_data_new/  ✅")
            except Exception as exc:
                p = future_to_partition[future]
                print(f"[{i:>3}/{total}] {p.name} ❌ 에러: {exc}")

    elapsed = (datetime.now() - job_start).total_seconds()
    print(f"전체 완료: {elapsed:.1f}초")


# ============================================================
# 3-2. HTTP 요청 병렬 처리
# ============================================================
def example_parallel_http():
    """여러 URL을 동시에 요청하는 패턴"""
    import requests

    urls = [
        "https://api.example.com/data/1",
        "https://api.example.com/data/2",
        "https://api.example.com/data/3",
    ]

    def fetch(url):
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return url, resp.json()

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(fetch, url): url for url in urls}

        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                _, data = future.result()
                print(f"✅ {url}: {len(data)} items")
            except Exception as exc:
                print(f"❌ {url}: {exc}")


# ============================================================
# 3-3. map() - 순서 보장이 필요할 때
# ============================================================
def example_ordered_map():
    """입력 순서대로 결과가 필요할 때 map() 사용"""
    import time

    def process(item):
        time.sleep(0.1)
        return item * 2

    items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    with ThreadPoolExecutor(max_workers=4) as executor:
        # 결과가 입력 순서대로 반환됨
        results = list(executor.map(process, items))
        print(results)  # [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]


# ============================================================
# 3-4. 진행률 표시 + 에러 수집
# ============================================================
def example_with_progress():
    """대량 작업 시 진행률과 에러를 추적하는 패턴"""
    import threading

    tasks = list(range(100))
    total = len(tasks)
    errors = []
    lock = threading.Lock()
    completed_count = 0

    def work(item):
        if item == 42:
            raise ValueError(f"Item {item} failed")
        return item * 2

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(work, t): t for t in tasks}

        for future in as_completed(futures):
            item = futures[future]
            try:
                future.result()
            except Exception as exc:
                with lock:
                    errors.append((item, str(exc)))

            with lock:
                completed_count += 1
                if completed_count % 10 == 0:
                    print(f"진행률: {completed_count}/{total} ({completed_count/total*100:.0f}%)")

    print(f"\n완료: {total - len(errors)}건 성공, {len(errors)}건 실패")
    if errors:
        print("실패 목록:")
        for item, err in errors:
            print(f"  - item={item}: {err}")


# ============================================================
# 3-5. 타임아웃 + 재시도
# ============================================================
def example_with_retry():
    """타임아웃과 재시도 로직이 포함된 패턴"""
    import time
    import random

    MAX_RETRIES = 3
    TIMEOUT_SEC = 5

    def unreliable_task(item):
        """가끔 실패하는 작업 시뮬레이션"""
        if random.random() < 0.3:
            raise ConnectionError(f"Temporary failure for {item}")
        time.sleep(0.5)
        return f"result_{item}"

    def task_with_retry(item):
        """재시도 래핑 (지수 백오프)"""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return unreliable_task(item)
            except Exception:
                if attempt == MAX_RETRIES:
                    raise
                time.sleep(0.5 * attempt)  # 지수 백오프

    items = list(range(20))

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(task_with_retry, i): i for i in items}

        for future in as_completed(futures, timeout=TIMEOUT_SEC):
            item = futures[future]
            try:
                result = future.result()
                print(f"✅ {item}: {result}")
            except Exception as exc:
                print(f"❌ {item}: {exc}")


# ############################################################
# PART 4: 주의사항 (Gotchas)
# ############################################################

# ============================================================
# 4-1. 데드락: 같은 executor에서 Future끼리 의존 금지
# ============================================================
# def task_a():
#     future_b = executor.submit(task_b)
#     return future_b.result()  # ← 데드락!
#
# max_workers=1이면 task_a가 유일한 스레드를 점유한 채
# task_b를 기다리므로 영원히 블록됨.
# max_workers가 많아도 모든 워커가 이런 상태면 데드락.

# ============================================================
# 4-2. 예외가 조용히 사라짐
# ============================================================
# future = executor.submit(buggy_function)
# # ← future.result()를 안 부르면 에러가 그냥 무시됨!
#
# 반드시 result()를 호출하거나 as_completed()로 순회해야 함

# ============================================================
# 4-3. map() 중 예외 → 이후 결과 접근 불가
# ============================================================
# for result in executor.map(risky_fn, items):
#     print(result)  # 하나 실패하면 여기서 멈춤!
#
# 해결: submit() + as_completed() 조합 사용

# ============================================================
# 4-4. 공유 상태 → Lock 필수
# ============================================================
# import threading
# lock = threading.Lock()
#
# def task(x):
#     result = compute(x)
#     with lock:
#         shared_list.append(result)  # 스레드 안전
#
# list.append()가 CPython에서 GIL 덕에 안전하긴 하지만
# 명시적 Lock 사용이 권장됨 (이식성, 명확성)

# ============================================================
# 4-5. GIL: CPU 바운드는 ThreadPool로 안 빨라짐
# ============================================================
# Python GIL = 한 번에 하나의 스레드만 Python 바이트코드 실행
#
# ThreadPoolExecutor가 빠른 경우:
#   I/O 대기 중에는 GIL 해제 → 다른 스레드 실행 가능
#   (HTTP, 파일, DB, S3 등)
#
# ThreadPoolExecutor가 안 빠른 경우:
#   순수 Python 연산 → GIL 때문에 결국 순차 실행
#   해결: ProcessPoolExecutor 또는 multiprocessing


# ############################################################
# PART 5: Databricks 노트북 전용 팁
# ############################################################

# ============================================================
# 5-1. dbutils는 드라이버 전용
# ============================================================
# ThreadPoolExecutor → 드라이버에서 실행 → dbutils 사용 가능 ✅
# sc.parallelize().foreach() → 워커에서 실행 → dbutils 못 씀 ❌
#
# 워커에서 S3 조작하려면 boto3 직접 사용해야 함

# ============================================================
# 5-2. S3 API 쓰로틀링
# ============================================================
# 같은 prefix에 대해:
#   PUT/COPY/POST/DELETE: 초당 3,500 요청
#   GET/HEAD:            초당 5,500 요청
#
# max_workers=10~20이 안전한 범위
# 100개 이상은 S3 503 SlowDown 에러 발생 가능

# ============================================================
# 5-3. Serverless 환경 주의사항
# ============================================================
# spark.conf.set()으로 설정 불가한 항목 있음
# 예: spark.sql.files.maxRecordsPerFile → CONFIG_NOT_AVAILABLE 에러
#
# 해결: DataFrameWriter .option() 사용
# df.write.option("maxRecordsPerFile", 1000).parquet(path)

# ============================================================
# 5-4. 노트북 복붙용 최소 코드
# ============================================================
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from datetime import datetime
#
# def move(p):
#     folder = p.name.rstrip("/")
#     src = f"s3://bucket/source/{folder}"
#     dst = f"s3://bucket/dest/{folder}"
#     dbutils.fs.cp(src, dst, recurse=True)
#     dbutils.fs.rm(src, recurse=True)
#     return folder
#
# partitions = dbutils.fs.ls("s3://bucket/source/")
# total = len(partitions)
# start = datetime.now()
#
# with ThreadPoolExecutor(max_workers=10) as ex:
#     futures = {ex.submit(move, p): p for p in partitions}
#     for i, f in enumerate(as_completed(futures), 1):
#         try:
#             print(f"[{i}/{total}] {f.result()} ✅")
#         except Exception as e:
#             print(f"[{i}/{total}] ❌ {e}")
#
# print(f"완료: {(datetime.now() - start).total_seconds():.1f}초")
