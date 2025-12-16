from time import sleep
from typing import Dict, Callable
from chapter1.epoll import Epoll
from chapter1.kernel import KernelSimulator

type Callback = Callable[[int], None]

class CallbackEventLoop:

    def __init__(self):
        self.epoll = Epoll(kernel=KernelSimulator())
        self.callback: Dict[int, Callback] = {}
        pass

    def register(self, fd: int, callback: Callback):
        self.epoll.epoll_ctl_add(fd, Epoll.READ)
        self.callback[fd] = callback

    def run_forever(self):
        while True:
            events = self.epoll.epoll_wait(max_events=3, timeout=5)
            for event in events:
                fd = event.fd
                callback = self.callback[fd]
                callback(fd)
                sleep(0.01)
