import random
import time
from threading import Thread

from message import CANMessage


class ECU(Thread):
    """
    A virtual ECU (node) on the bus. Each ECU has a fixed CAN ID and a
    generate_data() function that produces realistic-looking payload
    bytes for that signal, instead of an arbitrary random ID/string.

    Lower message_id = higher priority on the bus (matches real CAN,
    where safety-critical signals like braking get low IDs).
    """

    def __init__(self, name, message_id, bus, generate_data, period_range=(1, 3)):
        super().__init__(daemon=True)
        self.name = name
        self.message_id = message_id
        self.bus = bus
        self.generate_data = generate_data
        self.period_range = period_range

    def run(self):
        while True:
            data = self.generate_data()
            message = CANMessage(self.message_id, self.name, data)
            print(f"{self.name} generated -> {message}")
            self.bus.queue_message(message)
            time.sleep(random.uniform(*self.period_range))

    def receive_message(self, message):
        print(f"{self.name} received -> {message}")


# --- realistic per-ECU signal generators -------------------------------

def rpm_data():
    """Engine RPM as a 2-byte big-endian value (0 - 8000 RPM)."""
    rpm = random.randint(700, 6500)
    return [(rpm >> 8) & 0xFF, rpm & 0xFF]


def brake_pressure_data():
    """Brake pressure as a single byte, 0-255 (0-100% scaled)."""
    pressure = random.randint(0, 255)
    return [pressure]


def dashboard_status_data():
    """Dashboard heartbeat / status byte."""
    return [0x01]