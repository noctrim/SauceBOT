import time


class Timer:
    def __init__(self, mins):
        self.mins = mins
        self.timeout = 0

    def start(self):
        self.timeout = time.time() + self.mins * 60

    def is_active(self):
        return time.time() < self.timeout
