"""
Callback Hell v2: 에러 처리 추가

이제 각 단계마다 에러가 발생할 수 있다.
에러 처리를 추가하면 코드가 훨씬 더 복잡해진다.
"""

from time import sleep
from typing import Optional
from chapter1.kernel import KernelSimulator
from chapter2.callback_event_loop import CallbackEventLoop


def simulate_async_operation_with_error(
    kernel: KernelSimulator,
    loop: CallbackEventLoop,
    operation_name: str,
    should_fail: bool,
    callback
):
    """비동기 작업을 시뮬레이션 (에러 발생 가능)"""
    fd = kernel.create_socket()

    def on_ready(ready_fd: int):
        if should_fail:
            error = f"{operation_name} 실패!"
            callback(None, error)
        else:
            result = f"{operation_name} 결과"
            callback(result, None)

    loop.register(fd, on_ready)
    kernel.simulate_packet_arrival(fd, b"data")


def handle_request_with_error_handling(
    kernel: KernelSimulator,
    loop: CallbackEventLoop,
    client_fd: int,
    fail_at_step: Optional[int] = None
):
    """HTTP 요청 처리: 에러 처리 포함 (더 깊은 callback hell)"""

    print(f"[Step 0] 클라이언트 요청 시작 (fd={client_fd})")

    def handle_error(error_msg: str):
        print(f"!!! 에러 발생: {error_msg}")
        print(">>> 요청 처리 실패\n")

    def on_request_read(request_data, error):
        if error:
            return handle_error(error)

        print(f"[Step 1] 요청 읽기 완료: {request_data}")

        def on_db_result(db_data, error):
            if error:
                return handle_error(error)

            print(f"[Step 2] DB 조회 완료: {db_data}")

            def on_api_result(api_data, error):
                if error:
                    return handle_error(error)

                print(f"[Step 3] API 호출 완료: {api_data}")

                def on_response_sent(response, error):
                    if error:
                        return handle_error(error)

                    print(f"[Step 4] 응답 전송 완료: {response}")
                    print(">>> 모든 작업 완료!\n")

                simulate_async_operation_with_error(
                    kernel, loop, "응답 전송", fail_at_step == 4, on_response_sent
                )

            simulate_async_operation_with_error(
                kernel, loop, "API 호출", fail_at_step == 3, on_api_result
            )

        simulate_async_operation_with_error(
            kernel, loop, "DB 조회", fail_at_step == 2, on_db_result
        )

    simulate_async_operation_with_error(
        kernel, loop, "요청 읽기", fail_at_step == 1, on_request_read
    )


def main():
    kernel = KernelSimulator()
    loop = CallbackEventLoop()
    loop.epoll.kernel = kernel

    print("=== Callback Hell v2: 에러 처리 포함 ===\n")

    print("--- 케이스 1: 모든 단계 성공 ---\n")
    client_fd1 = kernel.create_socket()
    handle_request_with_error_handling(kernel, loop, client_fd1, fail_at_step=None)

    for _ in range(4):
        events = loop.epoll.epoll_wait(max_events=10, timeout=1)
        for event in events:
            callback = loop.callback[event.fd]
            callback(event.fd)
        sleep(0.1)

    print("\n--- 케이스 2: DB 조회에서 실패 ---\n")
    client_fd2 = kernel.create_socket()
    handle_request_with_error_handling(kernel, loop, client_fd2, fail_at_step=2)

    for _ in range(4):
        events = loop.epoll.epoll_wait(max_events=10, timeout=1)
        for event in events:
            callback = loop.callback[event.fd]
            callback(event.fd)
        sleep(0.1)


if __name__ == "__main__":
    main()
