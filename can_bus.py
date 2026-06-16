class CANBus:
    def __init__(self):
        self.ecus = []

    def connect(self,ecu):
        self.ecus.append(ecu)

    def queue_message(self,message):
        self.pending_messages.append(message)

    def process_bus(self):
        self.pending_messages.sort(
            key=lambda msg: msg.message.id
        )
        winner = self.pending_messages[0]

        print(f"\nWinner: {winner}")

        for ecu in self.ecus:
            if ecu.name != winner.sender:
                ecu.receive_message(winner)

        self.pending_messages.clear()