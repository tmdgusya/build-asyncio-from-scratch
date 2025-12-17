# Callback Hell

## 왜 불편한가?

Chapter 2에서 callback 기반 이벤트 루프를 만들었다. 간단한 에코 서버는 괜찮았다.
하지만 **순차적인 비동기 작업**이 필요하면? → Callback Hell

## 시나리오: HTTP 요청 처리

실제 웹 서버에서 자주 발생하는 상황:

```
1. 클라이언트 요청 읽기 (I/O 대기)
2. DB에서 데이터 조회 (I/O 대기)
3. 외부 API 호출 (I/O 대기)
4. 응답 보내기 (I/O 대기)
```

각 단계가 **비동기**이므로 callback으로 연결해야 한다.

## 문제 1: 가독성 (Readability)

### 동기 코드라면?

```python
request = read_request(client_fd)
db_data = query_database(request)
api_data = call_api(db_data)
send_response(client_fd, api_data)
```

위에서 아래로 읽으면 된다. 간단하다.

### Callback으로 작성하면?

```python
def handle_request(client_fd):
    def on_request_read(request_data):
        def on_db_result(db_data):
            def on_api_result(api_data):
                def on_response_sent(response):
                    print("완료!")
                send_response(client_fd, api_data, on_response_sent)
            call_api(db_data, on_api_result)
        query_database(request_data, on_db_result)
    read_request(client_fd, on_request_read)
```

**들여쓰기 지옥**. 오른쪽으로 계속 들어간다.
실행 순서를 파악하려면? 안쪽부터 거꾸로 읽어야 한다.

→ `callback_hell.py` 참고

## 문제 2: 에러 처리 (Error Handling)

각 단계에서 에러가 발생할 수 있다.
- 네트워크 끊김
- DB 연결 실패
- 외부 API 타임아웃

### Callback에서 에러 처리는?

```python
def handle_request(client_fd):
    def on_request_read(request_data, error):
        if error:
            return handle_error(client_fd, error)

        def on_db_result(db_data, error):
            if error:
                return handle_error(client_fd, error)

            def on_api_result(api_data, error):
                if error:
                    return handle_error(client_fd, error)

                def on_response_sent(response, error):
                    if error:
                        return handle_error(client_fd, error)
                    print("완료!")
                send_response(client_fd, api_data, on_response_sent)
            call_api(db_data, on_api_result)
        query_database(request_data, on_db_result)
    read_request(client_fd, on_request_read)
```

**매 단계마다 `if error` 체크**가 추가된다.
코드가 2배로 늘어난다. 가독성은 더 나빠진다.

→ `callback_hell_v2.py` 참고

## 문제 3: 변수 공유 (Variable Sharing)

여러 단계에서 같은 변수를 사용하고 싶다면?

```python
def handle_request(client_fd):
    user_id = None  # 여러 callback에서 사용

    def on_request_read(request_data):
        nonlocal user_id
        user_id = request_data['user_id']

        def on_db_result(db_data):
            # user_id 사용
            log(f"User {user_id}: DB query done")

            def on_api_result(api_data):
                # user_id 사용
                log(f"User {user_id}: API call done")
                ...
```

**클로저(closure)**로 변수를 공유해야 한다.
`nonlocal` 키워드를 써야 하고, 변수 스코프가 복잡해진다.

## 문제 4: 디버깅 (Debugging)

에러가 발생했을 때 스택 트레이스는?

```
Traceback (most recent call last):
  File "event_loop.py", line 26, in run_forever
    callback(fd)
  File "callback_hell.py", line 45, in on_api_result
    process_data(api_data)
```

**어디서 시작된 요청인지 알 수 없다.**

Callback은 이벤트 루프에서 개별적으로 실행되므로,
전체 흐름(요청 → DB → API → 응답)이 스택 트레이스에 나타나지 않는다.

## 문제 5: 취소/타임아웃 (Cancellation)

중간에 작업을 취소하고 싶다면?
- 클라이언트가 연결을 끊었다
- 타임아웃이 발생했다

```python
def handle_request(client_fd):
    cancelled = False

    def on_request_read(request_data):
        if cancelled:
            return

        def on_db_result(db_data):
            if cancelled:
                return

            def on_api_result(api_data):
                if cancelled:
                    return
                ...
```

**모든 callback에서 취소 여부를 체크**해야 한다.
타임아웃도 마찬가지로 모든 단계에 추가해야 한다.

## 정리: Callback의 한계

| 항목 | 문제점 |
|------|--------|
| **가독성** | 들여쓰기 지옥, 흐름 파악 어려움 |
| **에러 처리** | 매 단계마다 `if error` 필요 |
| **변수 공유** | 클로저, `nonlocal` 필요 |
| **디버깅** | 스택 트레이스가 의미없음 |
| **취소/타임아웃** | 모든 callback에 체크 코드 필요 |

## 그래서?

"**더 나은 방법 없나?**"

→ Chapter 4: Generator 기반 Coroutine으로 이 문제를 해결한다.

```python
# 이렇게 쓸 수 있다면?
def handle_request(client_fd):
    request = yield read_request(client_fd)
    db_data = yield query_database(request)
    api_data = yield call_api(db_data)
    yield send_response(client_fd, api_data)
    print("완료!")
```

평평하고(flat), 위에서 아래로 읽을 수 있고, 에러 처리도 간단해진다.
