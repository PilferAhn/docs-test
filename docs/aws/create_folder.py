import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import dbutils

# ============================================================
# 방법 1: 순차(Sequential) 방식 - 느린 이유
# ============================================================
# S3의 mkdirs()는 네트워크 I/O 작업이다.
# 순차 방식은 한 폴더 생성이 완료될 때까지 기다린 후에야
# 다음 폴더 생성을 시작한다.
#
# 타임라인: [mkdirs1] → [mkdirs2] → [mkdirs3] → ... → [mkdirs10]
#           (각 작업이 끝나야 다음 시작)
#
# 네트워크 왕복 지연(latency)이 폴더 개수만큼 누적되므로
# 총 소요 시간 ≈ 개별 latency × 폴더 수
# ============================================================
def create_folder1():
    s3_path = "s3://aws-s3-jimin-test/test/"
    start_num = 3

    for x in range(0, 10):
        # 루프를 돌 때마다 S3 API 호출을 하나씩 순서대로 실행
        # → 앞 요청의 응답이 올 때까지 CPU와 스레드가 그냥 대기(blocking)
        folder_name = "test" + str(start_num)
        start_num += 1
        path = os.path.join(s3_path, folder_name)
        dbutils.fs.mkdirs(path)  # 이 호출이 끝날 때까지 다음 줄로 진행 불가
        print(f"Created: {path}")


# ============================================================
# 방법 2: 병렬(Parallel) 방식 - 빠른 이유
# ============================================================
# ThreadPoolExecutor를 사용해 10개의 mkdirs() 호출을 동시에 실행한다.
# I/O 작업(네트워크 요청)은 GIL(Global Interpreter Lock)의 영향을 받지 않아
# 멀티스레드로 진정한 병렬 실행이 가능하다.
#
# 타임라인: [mkdirs1]
#           [mkdirs2]
#           [mkdirs3]  → 10개가 동시에 실행
#           ...
#           [mkdirs10]
#
# 총 소요 시간 ≈ 가장 오래 걸리는 단일 요청의 latency (약 1배)
# 방법 1 대비 최대 10배 빠름
# ============================================================
def create_folder2():

    s3_path = "s3://aws-s3-jimin-test/test/"
    start_num = 3

    def create_folder(folder_name):
        path = f"{s3_path}{folder_name}/"
        dbutils.fs.mkdirs(path)  # 각 스레드가 독립적으로 S3 API를 호출
        return path

    # 생성할 폴더명 목록을 미리 만들어 둠
    folder_names = [f"test{i}" for i in range(start_num, start_num + 10)]

    # max_workers=10: 폴더 수만큼 스레드를 생성해 모든 작업을 동시에 시작
    with ThreadPoolExecutor(max_workers=10) as executor:
        # executor.submit(): 각 폴더 생성 작업을 스레드풀에 제출 (즉시 반환)
        # futures dict: {Future객체: 폴더명} 매핑으로 결과 추적
        futures = {executor.submit(create_folder, name): name for name in folder_names}

        # as_completed(): 완료된 순서대로 결과를 받아 출력
        # (시작 순서가 아닌 완료 순서이므로 출력 순서가 매번 다를 수 있음)
        for future in as_completed(futures):
            print(f"Created: {future.result()}")


# ============================================================
# ThreadPoolExecutor 핵심 동작 원리
# ============================================================
# 결국 핵심은 이것:
#   "응답을 기다리지 않고 10개를 연달아 던진다"
#
# executor.submit()은 S3에 요청을 던지는 순간 바로 반환된다.
# 응답이 올 때까지 기다리지 않으므로 10개를 순식간에 모두 던질 수 있다.
# 각 스레드는 자기 응답이 올 때까지 독립적으로 대기하고,
# 완료된 것부터 as_completed()로 결과를 수거한다.
#
# [스레드1] → S3 요청 던짐 → (대기중...) → 응답 수신
# [스레드2] → S3 요청 던짐 → (대기중...) → 응답 수신
# ...
# [스레드10]→ S3 요청 던짐 → (대기중...) → 응답 수신
# → 10개 모두 거의 동시에 던지고, 거의 동시에 받음
#
# ※ 언제 쓰면 좋은가?
#   - I/O 작업 (S3, DB, API 호출 등): ✅ 매우 적합
#     → 대기 시간 동안 다른 스레드가 실행되므로 병렬 효과 최대
#   - CPU 집약 작업 (수치 계산, 이미지 처리 등): ❌ 부적합
#     → Python GIL(전역 잠금) 때문에 실제로는 동시 실행이 안 됨
#     → CPU 작업은 ThreadPoolExecutor 대신 ProcessPoolExecutor 사용
# ============================================================