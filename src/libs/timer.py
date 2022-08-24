import time


class Timer:
    """
    Timer class to check whether a certain amount of time has passed
    """
    def __init__(self):
        """
        Timer init
        """
        self.timeout = 0
        self.started = False

    def start(self, mins):
        """
        Start timer, can start timer again after started and it will restart

        :param mins: Minutes to set timer for
        """
        self.timeout = time.time() + mins * 60
        self.started = True

    def is_active(self):
        """
        Check if timer is currently active

        :return: bool if timer is active or not
        """
        return time.time() < self.timeout
