import os
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), "can_trace.log")


class CANLogger:
    """
    Produces a Wireshark-style trace of everything happening on the bus:
    arbitration results, successful deliveries, CRC errors, and
    retransmissions/drops. Writes to both the console and can_trace.log.
    """

    def __init__(self, log_file=LOG_FILE):
        self.log_file = log_file
        with open(self.log_file, "w") as f:
            f.write("TIMESTAMP\t\tID\tSENDER\t\tDATA\t\tDLC\tSTATUS\n")

    def _write(self, line):
        print(line)
        with open(self.log_file, "a") as f:
            f.write(line + "\n")

    def _ts(self):
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def log_arbitration(self, winner, losers):
        self._write(
            f"\n[{self._ts()}] ARBITRATION -> won by 0x{winner.message_id:03X} ({winner.sender})"
            + (f" | lost: {[f'0x{m.message_id:03X}' for m in losers]}" if losers else "")
        )

    def log_delivery(self, message):
        self._write(
            f"[{self._ts()}]  DELIVERED  ID=0x{message.message_id:03X} "
            f"Sender={message.sender:<12} Data={message.data} DLC={message.dlc} "
            f"CRC=0x{message.crc:02X}  [OK]"
        )

    def log_error(self, message):
        self._write(
            f"[{self._ts()}]  CRC ERROR  ID=0x{message.message_id:03X} "
            f"Sender={message.sender:<12} -> frame corrupted in transit, requesting retransmit"
        )

    def log_dropped(self, message):
        self._write(
            f"[{self._ts()}]  DROPPED    ID=0x{message.message_id:03X} "
            f"Sender={message.sender:<12} -> exceeded max retries, frame discarded"
        )
