
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class FileDescriptorState(Enum):
    READY = "ready"
    NOT_READY = "not_ready"


@dataclass
class KernelSocket:

    fd: int
    recv_buffer: List[bytes]
    send_buffer: List[bytes]

    def has_data_to_read(self) -> bool:
        return len(self.recv_buffer) > 0

    def can_write(self) -> bool:
        return len(self.send_buffer) < 10

class KernelSimulator:

    def __init__(self) -> None:
        self.sockets: Dict[int, KernelSocket] = {}
        self.next_fd = 3 # 0,1,2 는 standard input/output/error

    def create_socket(self) -> int:
        """socket() system call"""
        fd = self.next_fd
        self.next_fd += 1
        self.sockets[fd] = KernelSocket(fd, [], [])
        return fd

    def simulate_packet_arrival(self, fd: int, data: bytes) -> None:
        """recvfrom() system call"""
        if fd in self.sockets:
            self.sockets[fd].recv_buffer.append(data)

    def check_ready(self, fd: int, event_type: str) -> bool:

        if fd not in self.sockets:
            return False

        if event_type == "read":
            return self.sockets[fd].has_data_to_read()
        elif event_type == "write":
            return self.sockets[fd].can_write()
        return False
