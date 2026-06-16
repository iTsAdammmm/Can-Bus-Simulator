class CANBus:
    def __init__(self):
        self.ecus = []

    def connect(self,ecu):
        self.ecus.append(ecu)

    def transmit(self, message):
        print(
            f"\nTransmitting -> {message}"
        )
        for ecu in self.ecus:
            if ecu.name != message.sender:
                ecu.receive_message(message)