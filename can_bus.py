import time


class CANBus:

    def __init__(self):
        self.ecus = []
        self.pending_messages = []

    def connect(self, ecu):
        self.ecus.append(ecu)

    def queue_message(self, message):
        self.pending_messages.append(message)

    def process_bus(self):

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