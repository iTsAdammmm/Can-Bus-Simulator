from datetime import datetime


def compute_crc(data_bytes):
    """
    Simple CRC-8 (poly 0x07) over the data payload.
    Not the real 15-bit CAN CRC polynomial, but it demonstrates
    the same idea: a checksum the receiver can use to detect
    a corrupted frame.
    """
    crc = 0
    for byte in data_bytes:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


class CANMessage:
    """
    A simplified CAN 2.0A data frame.

    message_id : 11-bit standard identifier (0x000 - 0x7FF).
                 Lower value = higher priority on the bus.
    data       : list of up to 8 integers (0-255), i.e. the payload bytes.
    dlc        : Data Length Code, the real CAN field for payload length
                 in bytes (0-8) -- NOT the length of a string.
    crc        : checksum computed over the payload, used by the
                 receiver to detect a corrupted frame.
    """

    def __init__(self, message_id, sender, data, retries=0):
        if message_id < 0 or message_id > 0x7FF:
            raise ValueError("message_id must fit in an 11-bit standard CAN ID (0x000-0x7FF)")
        if len(data) > 8:
            raise ValueError("CAN payload cannot exceed 8 bytes")

        self.message_id = message_id
        self.sender = sender
        self.data = list(data)
        self.dlc = len(self.data)
        self.timestamp = datetime.now()
        self.crc = compute_crc(self.data)
        self.retries = retries  # how many times this frame has been retransmitted

    def corrupted_copy(self):
        """
        Simulate a transmission error: flip one bit in one payload byte.
        Returns a new CANMessage whose data no longer matches its
        original CRC once the receiver recomputes it.
        """
        corrupted_data = self.data.copy()
        if corrupted_data:
            corrupted_data[0] ^= 0x01
        bad = CANMessage(self.message_id, self.sender, corrupted_data, retries=self.retries)
        bad.crc = self.crc  # keep the OLD crc so it no longer matches the new data
        bad.timestamp = self.timestamp
        return bad

    def retransmit(self):
        """Return a copy of this message with the retry count incremented."""
        return CANMessage(self.message_id, self.sender, self.data, retries=self.retries + 1)

    def __str__(self):
        return (
            f"[ID=0x{self.message_id:03X}] "
            f"Sender={self.sender:<12} "
            f"DLC={self.dlc} "
            f"Data={self.data} "
            f"CRC=0x{self.crc:02X}"
            f"{' (retry ' + str(self.retries) + ')' if self.retries else ''}"
        )