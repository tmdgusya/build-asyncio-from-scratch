"""
select() 시스템 콜이 어떻게 동작하는지 보여주는 예시.

실제로는 커널이 하드웨어 인터럽트를 받아서 처리하지만,
여기서는 simulate_packet_arrival()로 "패킷이 도착했다"를 흉내낸다.
"""

import threading
from time import sleep
from chapter1.kernel import KernelSimulator
from chapter1.selector import Selector


def run_example():
    # 커널 초기화
    kernel = KernelSimulator()
    selector = Selector(kernel)

    # 소켓 2개 생성 (실제로는 socket() 시스템 콜)
    client_fd = kernel.create_socket()
    server_fd = kernel.create_socket()
    print(f"소켓 생성됨: client_fd={client_fd}, server_fd={server_fd}")

    # 별도 스레드에서 1초 후에 패킷 도착 시뮬레이션
    # (실제로는 NIC가 인터럽트를 걸고 커널이 버퍼에 데이터를 채움)
    def simulate_network():
        sleep(1)
        print("\n[커널] 패킷 도착! recv_buffer에 데이터 추가")
        kernel.simulate_packet_arrival(client_fd, b"Hello from network")

    threading.Thread(target=simulate_network, daemon=True).start()

    # select()로 대기 - 여기서 유저 모드 -> 커널 모드 전환이 일어남
    print("\nselect() 호출 - 데이터가 올 때까지 블로킹...")
    print("(유저 프로세스는 여기서 잠듦, CPU는 다른 프로세스 실행 가능)")

    ready_read, ready_write = selector.select(
        read_fds=[client_fd, server_fd],
        write_fds=[],
        timeout=5
    )

    # select()가 리턴됨 = 커널이 "준비됐다"고 깨워준 것
    print(f"\nselect() 리턴! ready_read={ready_read}")
    print(f"시스템 콜 횟수: {selector.syscall_count}")

    if client_fd in ready_read:
        # 이제 recv() 해도 블로킹 안 됨
        data = kernel.sockets[client_fd].recv_buffer.pop(0)
        print(f"수신된 데이터: {data}")


if __name__ == "__main__":
    run_example()
