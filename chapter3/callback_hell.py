"""
Callback Hell 예시: 순차적 비동기 작업을 callback으로 연결

시나리오:
1. 클라이언트 요청 읽기 (I/O)
2. DB 조회 (I/O)
3. 외부 API 호출 (I/O)
4. 응답 보내기 (I/O)
"""

from time import sleep
from chapter1.kernel import KernelSimulator
from chapter2.callback_event_loop import CallbackEventLoop


def simulate_async_operation(kernel: KernelSimulator, loop: CallbackEventLoop,
                             operation_name: str, callback):
    """비동기 작업을 시뮬레이션하는 헬퍼 함수"""
    fd = kernel.create_socket()

    def on_ready(ready_fd: int):
        result = f"{operation_name} 결과"
        callback(result)

    loop.register(fd, on_ready)

    kernel.simulate_packet_arrival(fd, b"data")


def handle_request(kernel: KernelSimulator, loop: CallbackEventLoop, client_fd: int):
    """HTTP 요청 처리: callback hell 발생"""

    print(f"[Step 0] 클라이언트 요청 시작 (fd={client_fd})")

    def on_request_read(request_data):
        print(f"[Step 1] 요청 읽기 완료: {request_data}")

        def on_db_result(db_data):
            print(f"[Step 2] DB 조회 완료: {db_data}")

            def on_api_result(api_data):
                print(f"[Step 3] API 호출 완료: {api_data}")

                def on_response_sent(response):
                    print(f"[Step 4] 응답 전송 완료: {response}")
                    print(">>> 모든 작업 완료!\n")

                simulate_async_operation(kernel, loop, "응답 전송", on_response_sent)

            simulate_async_operation(kernel, loop, "API 호출", on_api_result)

        simulate_async_operation(kernel, loop, "DB 조회", on_db_result)

    simulate_async_operation(kernel, loop, "요청 읽기", on_request_read)


def main():
    kernel = KernelSimulator()
    loop = CallbackEventLoop()
    loop.epoll.kernel = kernel

    print("=== Callback Hell 시연 ===\n")

    client_fd = kernel.create_socket()
    handle_request(kernel, loop, client_fd)

    print("이벤트 루프 실행 중...\n")

    for _ in range(4):
        events = loop.epoll.epoll_wait(max_events=10, timeout=1)
        for event in events:
            callback = loop.callback[event.fd]
            callback(event.fd)
        sleep(0.1)


if __name__ == "__main__":
    main()
