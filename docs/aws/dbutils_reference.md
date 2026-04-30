# Databricks dbutils 주요 명령어 레퍼런스

> 출처: [Databricks 공식문서](https://docs.databricks.com/en/dev-tools/databricks-utils.html) (2026.03 기준)

---

## 1. dbutils.fs (파일 시스템)

### ls - 디렉토리 목록 조회

```python
dbutils.fs.ls("/Volumes/main/default/my-volume/")
# Returns: [FileInfo(path='...', name='data.csv', size=2258987, modificationTime=1711357839000)]
```

### head - 파일 내용 미리보기

```python
dbutils.fs.head("/Volumes/main/default/my-volume/data.csv", 25)
# Returns: 'Year,First Name,County,Se'
```

- `max_bytes` (기본값: 65536)

### put - 파일 쓰기

```python
dbutils.fs.put("/Volumes/main/default/my-volume/hello.txt", "Hello, Databricks!", True)
```

- `overwrite` (기본값: False)

### cp - 파일 복사

```python
# 단일 파일
dbutils.fs.cp("/path/source.csv", "/path/dest.csv")

# 디렉토리 재귀 복사
dbutils.fs.cp("/path/source_dir", "/path/dest_dir", recurse=True)
```

### mv - 파일 이동 (복사 + 삭제)

```python
dbutils.fs.mv("/path/rows.csv", "/path/my-data/")

# 디렉토리 재귀 이동
dbutils.fs.mv("/path/source_dir", "/path/dest_dir", recurse=True)
```

> **참고:** mv는 내부적으로 copy + delete로 동작함 (같은 파일시스템 내에서도)

### rm - 파일/디렉토리 삭제

```python
# 단일 파일
dbutils.fs.rm("/path/old-file.csv")

# 디렉토리 재귀 삭제
dbutils.fs.rm("/path/my-data/", recurse=True)
```

### mkdirs - 디렉토리 생성

```python
dbutils.fs.mkdirs("/Volumes/main/default/my-volume/my-data")
# 부모 디렉토리도 자동 생성
```

---

## 2. dbutils.fs - Mount (S3/ADLS 마운트)

### mount - 외부 스토리지 마운트

```python
dbutils.fs.mount(
    source="s3a://my-bucket",
    mount_point="/mnt/s3-my-bucket",
    extra_configs={"key": "value"}
)
```

### mounts - 마운트 목록 조회

```python
dbutils.fs.mounts()
# [MountInfo(mountPoint='/mnt/databricks-results', source='databricks-results', encryptionType='sse-s3')]
```

### unmount - 마운트 해제

```python
dbutils.fs.unmount("/mnt/s3-my-bucket")
```

### refreshMounts - 마운트 갱신

```python
dbutils.fs.refreshMounts()
# 다른 클러스터에서 마운트 변경 후 반드시 호출
```

---

## 3. dbutils.secrets (시크릿 관리)

### listScopes - 스코프 목록

```python
dbutils.secrets.listScopes()
# [SecretScope(name='my-scope')]
```

### list - 스코프 내 시크릿 목록

```python
dbutils.secrets.list("my-scope")
# [SecretMetadata(key='my-key')]
```

### get - 시크릿 값 조회

```python
dbutils.secrets.get(scope="my-scope", key="my-key")
# 노트북에서는 '[REDACTED]'로 표시됨
```

### getBytes - 바이트 형태로 조회

```python
dbutils.secrets.getBytes(scope="my-scope", key="my-key")
# b'a1!b2@c3#'
```

---

## 4. dbutils.widgets (파라미터 위젯)

### 위젯 생성

```python
# 텍스트 입력
dbutils.widgets.text(name='user_name', defaultValue='', label='사용자명')

# 드롭다운
dbutils.widgets.dropdown(name='env', defaultValue='dev',
    choices=['dev', 'stg', 'prd'], label='환경')

# 콤보박스 (입력 + 선택)
dbutils.widgets.combobox(name='fruit', defaultValue='banana',
    choices=['apple', 'banana', 'coconut'], label='과일')

# 다중 선택
dbutils.widgets.multiselect(name='days', defaultValue='Monday',
    choices=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
    label='요일')
```

### 위젯 값 가져오기

```python
dbutils.widgets.get('env')        # 단일 위젯 값
dbutils.widgets.getAll()          # 모든 위젯 값 (Dict) - Runtime 13.3+
```

### SQL에서 위젯 사용

```sql
SELECT * FROM table WHERE env = :env
```

### 위젯 제거

```python
dbutils.widgets.remove('env')     # 특정 위젯 제거
dbutils.widgets.removeAll()       # 전체 제거
```

---

## 5. dbutils.notebook (노트북 오케스트레이션)

### run - 다른 노트북 실행

```python
result = dbutils.notebook.run("./child_notebook", timeout_seconds=60, arguments={"param1": "value1"})
# 자식 노트북의 exit 값 반환 (최대 5MB)
```

### exit - 노트북 종료 및 값 반환

```python
dbutils.notebook.exit("SUCCESS")
# 호출한 노트북에 값을 반환하며 종료
```

---

## 6. dbutils.jobs.taskValues (Job 태스크 간 값 전달)

### set - 값 설정 (Python only)

```python
dbutils.jobs.taskValues.set(key="my_key", value={"count": 100})
# 실행당 최대 250개, 값당 최대 48KB JSON
```

### get - 업스트림 태스크 값 조회 (Python only)

```python
dbutils.jobs.taskValues.get(taskKey="upstream_task", key="my_key", default="N/A")
```

---

## 7. dbutils.library (라이브러리)

### restartPython - Python 프로세스 재시작

```python
dbutils.library.restartPython()
# pip install 후 라이브러리를 현재 세션에 반영할 때 사용
```

---

## Quick Reference Table

| 카테고리 | 명령어 | 용도 |
|---------|--------|------|
| **파일** | `fs.ls` | 목록 조회 |
| **파일** | `fs.head` | 내용 미리보기 |
| **파일** | `fs.put` | 파일 쓰기 |
| **파일** | `fs.cp` | 복사 |
| **파일** | `fs.mv` | 이동 |
| **파일** | `fs.rm` | 삭제 |
| **파일** | `fs.mkdirs` | 디렉토리 생성 |
| **마운트** | `fs.mount` | 외부 스토리지 연결 |
| **마운트** | `fs.unmount` | 마운트 해제 |
| **시크릿** | `secrets.get` | 비밀값 조회 |
| **시크릿** | `secrets.list` | 키 목록 조회 |
| **위젯** | `widgets.get` | 파라미터 값 조회 |
| **위젯** | `widgets.dropdown` | 드롭다운 생성 |
| **노트북** | `notebook.run` | 자식 노트북 실행 |
| **노트북** | `notebook.exit` | 값 반환 및 종료 |
| **Job** | `jobs.taskValues.set/get` | 태스크 간 값 전달 |
