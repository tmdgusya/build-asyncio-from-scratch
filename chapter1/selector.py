from time import sleep, time
from chapter1.kernel import KernelSimulator
from typing import List

class Selector:

    def __init__(self, kernel: KernelSimulator) -> None:
        self.kernel = kernel
        self.syscall_count = 0

    def select(self, read_fds: List[int], write_fds: List[int], timeout: int) -> tuple[List[int], List[int]]:
        self.syscall_count = 1

        start_time = time()
        ready_read = []
        ready_write = []

        while True:
            for fd in read_fds:
                if self.kernel.check_ready(fd, "read"):
                    ready_read.append(fd)

            for fd in write_fds:
                if self.kernel.check_ready(fd, "write"):
                    ready_write.append(fd)

            if ready_read or ready_write:
                break;

            if timeout and (time() - start_time) > timeout:
                print("Timeout occurred")
                break

            sleep(0.01)

        return ready_read, ready_write
