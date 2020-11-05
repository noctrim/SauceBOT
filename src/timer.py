import time


class Timer:
    """
    Timer class to check whether a certain amount of time has passed
    """
    def __init__(self, mins):
        """
        Timer init
        :param mins: Minutes to set timer for
        """
        self.mins = mins
        self.timeout = 0

    def start(self):
        """
        Start timer, can start timer again after started and it will restart
        """
        self.timeout = time.time() + self.mins * 60

    def is_active(self):
        """
        Check if timer is currently active

        :return: bool if timer is active or not
        """
        return time.time() < self.timeout
