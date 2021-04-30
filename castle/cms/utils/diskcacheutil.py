from diskcache import Deque


class DequeUtil():

    def __init__(self):
        self.deque = Deque()

    def add_to_deque(self, data):
        self.deque.append(data)
