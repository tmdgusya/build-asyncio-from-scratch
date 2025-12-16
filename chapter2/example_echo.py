"""
에코 서버 예시: 3개의 클라이언트가 메시지를 보내면 각각 에코해주는 예시
callback이 각각 실행되는 것을 보여줌
"""

from chapter1.kernel import KernelSimulator
from chapter2.callback_event_loop import CallbackEventLoop


def main():
    # 1. 커널과 이벤트 루프 생성
    kernel = KernelSimulator()
    loop = CallbackEventLoop()
    loop.epoll.kernel = kernel  # 동일한 커널 사용

    # 2. 3개의 클라이언트 소켓 생성
    client1_fd = kernel.create_socket()
    client2_fd = kernel.create_socket()
    client3_fd = kernel.create_socket()

    print(f"클라이언트 소켓 생성 완료: fd={client1_fd}, {client2_fd}, {client3_fd}")

    # 3. 각 클라이언트에 대한 에코 callback 정의
    def echo_callback(fd: int):
        """데이터를 읽어서 에코"""
        socket = kernel.sockets[fd]
        if socket.recv_buffer:
            data = socket.recv_buffer.pop(0)  # 첫 번째 데이터 읽기
            message = data.decode('utf-8')
            print(f"[fd={fd}] 받은 메시지: '{message}'")
            print(f"[fd={fd}] 에코: '{message}'")
            print()

    # 4. 각 클라이언트 fd를 이벤트 루프에 등록
    loop.register(client1_fd, echo_callback)
    loop.register(client2_fd, echo_callback)
    loop.register(client3_fd, echo_callback)

    print("모든 클라이언트를 이벤트 루프에 등록 완료\n")

    # 5. 시뮬레이션: 각 클라이언트가 메시지 전송
    print("=== 메시지 전송 시뮬레이션 시작 ===\n")

    kernel.simulate_packet_arrival(client1_fd, b"Hello from client 1")
    kernel.simulate_packet_arrival(client2_fd, b"Hello from client 2")
    kernel.simulate_packet_arrival(client3_fd, b"Hello from client 3")

    # 6. 이벤트 루프 실행 (한 번만 돌려서 테스트)
    print("=== 이벤트 루프 실행 ===\n")

    # run_forever()는 무한 루프이므로, 한 번만 돌리기 위해 직접 epoll_wait 호출
    events = loop.epoll.epoll_wait(max_events=3, timeout=1)
    print(f"감지된 이벤트: {len(events)}개\n")

    for event in events:
        fd = event.fd
        callback = loop.callback[fd]
        callback(fd)


if __name__ == "__main__":
    main()
