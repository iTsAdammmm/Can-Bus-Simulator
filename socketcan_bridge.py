import can

CHANNEL = "vcan0"
BUSTYPE = "socketcan"


class SocketCANBridge:
    """
    Wraps a python-can Bus connected to a real/virtual CAN interface.
    Used to mirror messages the simulator delivers onto the OS-level bus,
    and to listen for frames injected from outside (e.g. via `cansend`).
    """

    def __init__(self, channel=CHANNEL, bustype=BUSTYPE):
        self.bus = can.interface.Bus(channel=channel, bustype=bustype)

    def send(self, can_message):
        """
        Take one of our simulator's CANMessage objects and send it as a
        real frame on the SocketCAN interface.
        """
        frame = can.Message(
            arbitration_id=can_message.message_id,
            data=bytes(can_message.data),
            dlc=can_message.dlc,
            is_extended_id=False,
        )
        try:
            self.bus.send(frame)
        except can.CanError as e:
            print(f"[SocketCAN] failed to send frame: {e}")

    def listen(self, on_frame):
        """
        Blocking loop that reads frames arriving on the SocketCAN interface
        (e.g. sent externally via `cansend vcan0 123#DEADBEEF`) and invokes
        on_frame(msg) for each one. Meant to be run in its own thread.
        """
        for frame in self.bus:
            on_frame(frame)

    def shutdown(self):
        self.bus.shutdown()
