import random
import time
from threading import Lock

from message import compute_crc
from logger import CANLogger

# Real-world CAN bus error rate is a small fraction of a percent.
# Bumped up here so errors/retransmits actually show up in a short demo run.
ERROR_INJECTION_PROBABILITY = 0.15

# Standard CAN IDs are 11 bits wide (0x000 - 0x7FF).
ID_BIT_WIDTH = 11


class CANBus:

    def __init__(self, socketcan_bridge=None):
        self.ecus = []
        self.pending_messages = []
        self.lock = Lock()
        self.logger = CANLogger()
        # Optional: mirror every successfully delivered frame onto a real/
        # virtual CAN interface via python-can (see socketcan_bridge.py).
        # None means "pure simulation, no OS-level CAN interface".
        self.socketcan_bridge = socketcan_bridge

    def connect(self, ecu):
        self.ecus.append(ecu)

    def queue_message(self, message):
        """
        Add a message to the pending queue. If this sender already has a
        pending frame with the same ID waiting for arbitration, replace
        it instead of appending -- a real ECU's transmit buffer holds
        only the latest value for a given signal, not a backlog of
        stale ones. Without this, a low-priority ECU that keeps losing
        arbitration would pile up duplicate frames instead of the older
        value being superseded.
        """
        with self.lock:
            for i, existing in enumerate(self.pending_messages):
                if existing.sender == message.sender and existing.message_id == message.message_id:
                    self.pending_messages[i] = message
                    return
            self.pending_messages.append(message)

    @staticmethod
    def _arbitrate(contenders):
        """
        Simulate real CAN bus arbitration bit-by-bit instead of just
        sorting by ID.

        On the physical bus, 0 is the "dominant" bit and 1 is "recessive":
        while transmitting its identifier, every node also reads the bus
        and if it sent a recessive (1) bit but sees a dominant (0) bit
        (because another node pulled the line low), it knows it lost and
        immediately stops transmitting. This repeats bit by bit, from the
        most significant bit down, until only one node is left -- that
        node has the numerically lowest ID and wins the bus non-destructively
        (no collision, no wasted bandwidth, unlike Ethernet-style backoff).
        """
        for bit_pos in range(ID_BIT_WIDTH - 1, -1, -1):
            if len(contenders) <= 1:
                break

            bits = [(msg, (msg.message_id >> bit_pos) & 1) for msg in contenders]
            dominant_present = any(bit == 0 for _, bit in bits)

            if dominant_present:
                # anyone transmitting a recessive (1) bit here loses and backs off
                contenders = [msg for msg, bit in bits if bit == 0]

        return contenders[0], contenders[1:]

    def process_bus(self):

        with self.lock:
            if not self.pending_messages:
                return

            winner, _ = self._arbitrate(self.pending_messages)

            # everyone who didn't win goes back on the queue to
            # re-attempt arbitration next cycle, exactly like real CAN
            losers = [m for m in self.pending_messages if m is not winner]
            self.pending_messages = losers

        self.logger.log_arbitration(winner, losers)
        self._deliver(winner)

    def _deliver(self, message):
        """
        Deliver the arbitration winner to every other ECU, simulating an
        occasional transmission error along the way (a bit flips in
        transit). Receivers detect this via CRC mismatch and the sender
        retransmits, just like a real CAN error frame + retry.
        """
        corrupted_in_transit = random.random() < ERROR_INJECTION_PROBABILITY
        frame_on_wire = message.corrupted_copy() if corrupted_in_transit else message

        # receiver-side CRC check
        recomputed = compute_crc(frame_on_wire.data)
        if recomputed != frame_on_wire.crc:
            self.logger.log_error(message)
            if message.retries < 3:
                self.queue_message(message.retransmit())
            else:
                self.logger.log_dropped(message)
            return

        self.logger.log_delivery(frame_on_wire)
        if self.socketcan_bridge is not None:
            self.socketcan_bridge.send(frame_on_wire)
        for ecu in self.ecus:
            if ecu.name != message.sender:
                ecu.receive_message(frame_on_wire)

    def start(self):
        while True:
            if self.pending_messages:
                self.process_bus()
            time.sleep(1)