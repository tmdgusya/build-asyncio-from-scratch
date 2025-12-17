from dataclasses import dataclass
from typing import Dict, List, Set
from time import sleep, time

from chapter1.kernel import KernelSimulator


@dataclass
class EpollEvent:
    fd: int
    events: int

class Epoll:

    READ = 1

    def __init__(self, kernel: KernelSimulator) -> None:
        self.kernel = kernel
        self.interest_list: Dict[int, int] = {}

        self.ready_list: List[EpollEvent] = []
        self._ready_set: Set[int] = set()
        self.syscall_count = 0

    def epoll_ctl_add(self, fd: int, events: int):
        self.syscall_count = 1

        # 관심 목록에 해당 event 등록
        self.interest_list[fd] = events

        if fd in self.kernel.sockets:
            socket = self.kernel.sockets[fd]

            def on_event(event_fd: int, event_type: str):

                if event_fd not in self._ready_set:
                    self._ready_set.add(event_fd)
                    self.ready_list.append(EpollEvent(event_fd, events=1))

            socket.wait_queue.append(on_event)

    def epoll_wait(self, max_events: int, timeout: float = 10.0) -> List[EpollEvent]:
        self.syscall_count += 1

        start_time = time()
        wait_count = 0

        while not self.ready_list:
            wait_count += 1

            elapsed_time = time() - start_time
            if elapsed_time >= timeout:
                print(f"Timeout reached after {wait_count} waits")
                break

            sleep(0.1)


        result = self.ready_list[:max_events]
        self.ready_list = self.ready_list[max_events:]

        for event in result:
            self._ready_set.discard(event.fd)


        return result
