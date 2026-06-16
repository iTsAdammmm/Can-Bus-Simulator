class ECU:
    def __init__(self,name):
        self.name = name
    def receive_message(self, message):
        print(
            f"{self.name} received -> {message}"
        )