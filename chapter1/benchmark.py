"""
select() vs epoll() 성능 비교.

핵심 차이:
- select: 매번 모든 fd 목록을 커널에 전달 → O(n) 복사 비용
- epoll: 관심 목록은 커널에 한번만 등록, wait만 호출 → O(1) 대기
"""

import threading
import random
from time import sleep, time
from chapter1.kernel import KernelSimulator
from chapter1.selector import Selector
from chapter1.epoll import Epoll, EpollEvent


def benchmark_selector(num_clients: int):
    kernel = KernelSimulator()
    selector = Selector(kernel)

    # 소켓 생성
    fds = [kernel.create_socket() for _ in range(num_clients)]

    # 랜덤하게 일부 소켓에 데이터 도착 시뮬레이션
    for fd in random.sample(fds, min(100, num_clients)):
        kernel.simulate_packet_arrival(fd, b"data")

    # select 호출 - 매번 전체 fd 리스트를 전달해야 함
    start = time()
    for _ in range(10):  # 10번 반복
        ready, _ = selector.select(read_fds=fds, write_fds=[], timeout=0.001)
    elapsed = time() - start

    return elapsed, selector.syscall_count


def benchmark_epoll(num_clients: int):
    kernel = KernelSimulator()
    epoll = Epoll(kernel)

    # 소켓 생성
    fds = [kernel.create_socket() for _ in range(num_clients)]

    # epoll_ctl로 관심 목록에 한번만 등록 (최초 1회)
    start_register = time()
    for fd in fds:
        epoll.epoll_ctl_add(fd, events=1)
    register_time = time() - start_register

    # 매번 100개씩 ready 상태로 만들고 wait 호출
    start = time()
    for _ in range(10):
        # 커널이 ready_list에 이벤트 추가 (시뮬레이션)
        for fd in random.sample(fds, 100):
            if fd not in epoll._ready_set:
                epoll._ready_set.add(fd)
                epoll.ready_list.append(EpollEvent(fd=fd, events=1))

        # epoll_wait - fd 목록 전달 필요 없음, ready된 것만 받음
        events = epoll.epoll_wait(max_events=100, timeout=0.001)
    elapsed = time() - start

    return elapsed, epoll.syscall_count, register_time


def run_benchmark():
    num_clients = 2000

    print(f"벤치마크: {num_clients}개 소켓 처리")
    print("=" * 50)

    # Selector 벤치마크
    selector_time, selector_syscalls = benchmark_selector(num_clients)
    print(f"\n[select()]")
    print(f"  소요 시간: {selector_time:.4f}초")
    print(f"  syscall 횟수: {selector_syscalls}")
    print(f"  매 호출마다 {num_clients}개 fd를 커널에 복사")

    # Epoll 벤치마크
    epoll_time, epoll_syscalls, register_time = benchmark_epoll(num_clients)
    print(f"\n[epoll()]")
    print(f"  등록 시간: {register_time:.4f}초 (최초 1회)")
    print(f"  wait 시간: {epoll_time:.4f}초")
    print(f"  syscall 횟수: {epoll_syscalls}")
    print(f"  wait 호출 시 fd 목록 전달 불필요")

    print("\n" + "=" * 50)
    print("결론:")
    print(f"  select는 매번 O({num_clients}) 복사 발생")
    print(f"  epoll은 등록 후 O(ready 개수)만 처리")
    print(f"  연결 수가 많을수록 epoll이 유리")


if __name__ == "__main__":
    run_benchmark()
