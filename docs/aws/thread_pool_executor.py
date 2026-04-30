# ============================================================
# Python ThreadPoolExecutor 완전 가이드
# ============================================================
# 모듈: concurrent.futures (표준 라이브러리, 설치 불필요)
# 용도: I/O 바운드 작업의 병렬 처리 (HTTP, S3, DB, 파일 I/O)
# 주의: CPU 바운드 작업은 GIL 때문에 효과 없음 → ProcessPoolExecutor 사용
# ============================================================

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
# 1. 클래스 시그니처
# ============================================================
# ThreadPoolExecutor(
#     max_workers=None,          # 최대 스레드 수 (None이면 min(32, cpu_count+4))
#     thread_name_prefix='',     # 스레드 이름 접두사 (디버깅용)
#     initializer=None,          # 각 워커 스레드 시작 시 호출할 함수
#     initargs=()                # initializer에 전달할 인자
# )


# ============================================================
# 2. 핵심 메서드
# ============================================================

# --- submit(): 단일 작업 제출, Future 반환 ---
# future = executor.submit(fn, *args, **kwargs)
# - 가장 유연한 방식
# - Future 객체로 결과/예외를 개별 제어 가능

# --- map(): 여러 작업 일괄 제출, 결과 순서 보장 ---
# results = executor.map(fn, iterable, timeout=None)
# - 입력 순서대로 결과 반환 (완료 순서 아님!)
# - 중간에 예외 발생 시 이후 결과 접근 불가

# --- shutdown(): 종료 ---
# executor.shutdown(wait=True, cancel_futures=False)
# - with문 사용 시 자동 호출됨


# ============================================================
# 3. Future 객체 메서드
# ============================================================
# future.result(timeout=None)   # 결과 반환 (예외 시 re-raise)
# future.exception(timeout=None)# 예외 반환 (없으면 None)
# future.done()                 # 완료 여부 (bool)
# future.cancelled()            # 취소 여부 (bool)
# future.cancel()               # 취소 시도 (실행 전만 가능)
# future.running()              # 실행 중 여부
# future.add_done_callback(fn)  # 완료 시 콜백 등록


# ============================================================
# 4. 모듈 함수
# ============================================================
# as_completed(futures, timeout=None)
#   - 완료된 순서대로 Future를 yield (빠른 것부터!)
#   - 결과를 빨리 처리하고 싶을 때 사용
#
# wait(futures, timeout=None, return_when=ALL_COMPLETED)
#   - (done, not_done) 집합 반환
#   - return_when: FIRST_COMPLETED, FIRST_EXCEPTION, ALL_COMPLETED


# ============================================================
# 5. 실전 예시: S3 파티션 병렬 이동 (Databricks)
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
# 6. 실전 예시: HTTP 요청 병렬 처리
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
# 7. 실전 예시: map() - 순서 보장이 필요할 때
# ============================================================
def example_ordered_map():
    """입력 순서대로 결과가 필요할 때 map() 사용"""

    def process(item):
        # 시뮬레이션: 각 아이템 처리
        import time
        time.sleep(0.1)
        return item * 2

    items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    with ThreadPoolExecutor(max_workers=4) as executor:
        # 결과가 입력 순서대로 반환됨
        results = list(executor.map(process, items))
        print(results)  # [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]


# ============================================================
# 8. 실전 예시: 진행률 표시 + 에러 수집
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
        # 실제 작업
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
# 9. 실전 예시: 타임아웃 + 재시도
# ============================================================
def example_with_retry():
    """타임아웃과 재시도 로직이 포함된 패턴"""
    import time

    MAX_RETRIES = 3
    TIMEOUT_SEC = 5

    def unreliable_task(item):
        """가끔 실패하는 작업 시뮬레이션"""
        import random
        if random.random() < 0.3:
            raise ConnectionError(f"Temporary failure for {item}")
        time.sleep(0.5)
        return f"result_{item}"

    def task_with_retry(item):
        """재시도 래핑"""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return unreliable_task(item)
            except Exception as exc:
                if attempt == MAX_RETRIES:
                    raise
                time.sleep(0.5 * attempt)  # 백오프

    items = list(range(20))

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(task_with_retry, i): i for i in items}

        # 타임아웃 적용
        for future in as_completed(futures, timeout=TIMEOUT_SEC):
            item = futures[future]
            try:
                result = future.result()
                print(f"✅ {item}: {result}")
            except Exception as exc:
                print(f"❌ {item}: {exc}")


# ============================================================
# 10. max_workers 가이드
# ============================================================
# | 작업 유형           | 권장 max_workers       | 이유                    |
# |--------------------|-----------------------|------------------------|
# | S3/HTTP I/O        | 10~50                 | 대부분 대기 시간이라 많아도 OK  |
# | DB 쿼리            | 커넥션 풀 크기와 동일     | 풀 초과 시 의미 없음         |
# | 파일 I/O           | 5~20                  | 디스크 처리량 한계           |
# | CPU 바운드          | 1 (사용하지 말 것)       | GIL 때문에 효과 없음         |
# | Databricks dbutils | 10~20                 | S3 API 쓰로틀링 고려       |


# ============================================================
# 11. 주의사항 (Gotchas)
# ============================================================

# ❌ 데드락: 같은 executor에서 Future끼리 의존하면 안 됨
# def task_a():
#     future_b = executor.submit(task_b)
#     return future_b.result()  # ← 데드락 가능!

# ❌ 예외 무시: future.result()를 안 부르면 예외가 조용히 사라짐
# future = executor.submit(buggy)  # 에러 발생해도 아무 일도 안 일어남

# ❌ map() 중 예외: 하나 실패하면 이후 결과 접근 불가
# 해결: submit() + as_completed() 사용

# ❌ 공유 상태: 스레드는 메모리 공유 → Lock 필요
# import threading
# lock = threading.Lock()
# with lock:
#     shared_list.append(value)

# ❌ GIL: CPU 바운드 작업은 ThreadPool로 빨라지지 않음
# 해결: ProcessPoolExecutor 또는 multiprocessing 사용


# ============================================================
# 12. submit() vs map() 선택 가이드
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


# ============================================================
# 13. Databricks 노트북 전용 팁
# ============================================================
# 1) dbutils는 드라이버 노드에서만 사용 가능
#    → ThreadPoolExecutor는 드라이버에서 실행되므로 OK
#    → sc.parallelize().foreach() 안에서는 dbutils 못 씀
#
# 2) Databricks Runtime의 Python은 GIL 있음 (일반 CPython)
#    → I/O (S3 복사/삭제)에는 ThreadPool이 효과적
#
# 3) S3 API 쓰로틀링 주의
#    → 같은 prefix에 대해 초당 3,500 PUT / 5,500 GET 제한
#    → max_workers=10~20 정도가 안전
#
# 4) 노트북에서 바로 실행 가능한 최소 코드:
#
# from concurrent.futures import ThreadPoolExecutor, as_completed
#
# def move(p):
#     src = f"s3://bucket/source/{p.name.rstrip('/')}"
#     dst = f"s3://bucket/dest/{p.name.rstrip('/')}"
#     dbutils.fs.cp(src, dst, recurse=True)
#     dbutils.fs.rm(src, recurse=True)
#     return p.name
#
# with ThreadPoolExecutor(max_workers=10) as ex:
#     futures = {ex.submit(move, p): p for p in partitions}
#     for f in as_completed(futures):
#         print(f.result())
