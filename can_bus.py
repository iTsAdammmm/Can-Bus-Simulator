import time
from threading import Lock


class CANBus:

    def __init__(self):
        self.ecus = []
        self.pending_messages = []
        self.lock= Lock()

    def connect(self, ecu):
        self.ecus.append(ecu)

    def queue_message(self, message):
        with self.lock:
            self.pending_messages.append(message)

    def process_bus(self):

        with self.lock:    
            if not self.pending_messages:
                return

            self.pending_messages.sort(
                key=lambda msg: msg.message_id
            )

            winner = self.pending_messages[0]

            print("\n==============================")
            print(f"Winner -> {winner}")
            print("==============================")

            for ecu in self.ecus:
                if ecu.name != winner.sender:
                    ecu.receive_message(winner)

            self.pending_messages.clear()

    def start(self):

        while True:

            if self.pending_messages:
                self.process_bus()

            time.sleep(1)