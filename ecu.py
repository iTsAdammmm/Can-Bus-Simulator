from threading import Thread
from message import CANMessage
import time
import random


class ECU(Thread):

    def __init__(self, name, bus):
        super().__init__()
        self.name = name
        self.bus = bus

    def run(self):

        while True:

            message = CANMessage(
                random.randint(50, 300),
                self.name,
                f"Data from {self.name}"
            )

            print(f"{self.name} generated -> {message}")

            self.bus.queue_message(message)

            time.sleep(random.randint(1, 3))

    def receive_message(self, message):
        print(f"{self.name} received -> {message}")