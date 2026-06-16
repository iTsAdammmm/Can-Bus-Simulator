from datetime import datetime

class CANMessage:
    def __init__(self, message_id, sender, data):
        self.message_id = message_id
        self.sender = sender
        self.data = data

        self.timestamp = datetime.now()
        self.dlc = len(str(data))
    
    def __str__(self):
        return(
            f"[ID={self.message_id}] "
            f"Sender={self.sender} "
            f"Data={self.data}"
        )