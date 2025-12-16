"""
여러 클라이언트 연결을 select()로 동시에 처리하는 예시.

핵심: 하나의 스레드에서 여러 I/O를 "동시에" 기다릴 수 있다.
패킷이 도착한 순서대로 처리되므로, 늦게 요청해도 빨리 응답오면 먼저 처리됨.
"""

import threading
import random
from time import sleep, time
from chapter1.kernel import KernelSimulator
from chapter1.selector import Selector


def run_example():
    kernel = KernelSimulator()
    selector = Selector(kernel)

    # 클라이언트 5개 연결 시뮬레이션
    clients = {}
    for i in range(5):
        fd = kernel.create_socket()
        clients[fd] = f"Client-{i+1}"
        print(f"{clients[fd]} 연결됨 (fd={fd})")

    print("\n" + "="*50)
    print("각 클라이언트에서 랜덤한 시간 후 응답이 옴")
    print("="*50 + "\n")

    # 각 클라이언트마다 랜덤한 시간 후에 패킷 도착
    def simulate_response(fd, name, delay):
        sleep(delay)
        msg = f"{name}의 응답 (지연: {delay:.1f}초)"
        kernel.simulate_packet_arrival(fd, msg.encode())
        print(f"  [커널] {name} 패킷 도착!")

    # 스레드로 네트워크 지연 시뮬레이션
    for fd, name in clients.items():
        delay = random.uniform(0.3, 2.0)
        threading.Thread(
            target=simulate_response,
            args=(fd, name, delay),
            daemon=True
        ).start()

    # 이벤트 루프 - 모든 클라이언트 응답 받을 때까지 반복
    pending_fds = set(clients.keys())
    start = time()

    while pending_fds:
        # select()로 준비된 fd들 확인
        ready, _ = selector.select(
            read_fds=list(pending_fds),
            write_fds=[],
            timeout=5
        )

        # 준비된 것들만 처리 (블로킹 없음!)
        for fd in ready:
            data = kernel.sockets[fd].recv_buffer.pop(0)
            elapsed = time() - start
            print(f"[{elapsed:.2f}s] 수신: {data.decode()}")
            pending_fds.remove(fd)

    print(f"\n총 소요 시간: {time() - start:.2f}초")
    print("(순차 처리였다면 각 지연시간의 합만큼 걸렸을 것)")


if __name__ == "__main__":
    run_example()
