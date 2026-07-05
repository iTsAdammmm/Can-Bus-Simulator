# CAN Bus Communication Simulator

A Python-based simulation of CAN (Controller Area Network) communication between
multiple Electronic Control Units (ECUs), modeling real CAN 2.0A frame structure,
bit-level bus arbitration, and CRC-based error detection with retransmission.

## What it simulates

- **3 virtual ECUs** on a shared bus: a Brake ECU, an Engine ECU, and a Dashboard ECU,
  each periodically transmitting a realistic signal (brake pressure, RPM, status heartbeat).
- **CAN 2.0A frame structure**: 11-bit standard identifier, payload of up to 8 data bytes,
  a proper Data Length Code (DLC), and a CRC checksum over the payload.
- **Bit-level bus arbitration**: instead of just sorting by ID, the simulator walks the
  identifier bit-by-bit (MSB first) the way a real CAN transceiver does. At each bit, any
  node transmitting a recessive (`1`) bit while another node drives a dominant (`0`) bit
  loses arbitration and backs off immediately. This is a non-destructive priority
  mechanism, unlike collision-based protocols such as Ethernet's CSMA/CD. Since brake
  data uses the lowest ID (`0x100`), it wins arbitration against the engine (`0x200`)
  and dashboard (`0x300`) whenever they contend for the bus at the same time.
- **CRC error detection and retransmission**: a small percentage of "delivered" frames
  are corrupted in transit to simulate line noise. The receiver recomputes the CRC over
  the payload; on a mismatch it's treated as an error frame and the sender retransmits
  (up to 3 attempts before the frame is dropped) -- mirroring real CAN's automatic
  retransmission behavior.
- **Realistic TX-buffer behavior**: if an ECU generates a new value before its previous
  one has won arbitration, the old pending frame is replaced rather than queued
  alongside it -- just like a real transmit buffer, which only ever holds the latest
  value for a given signal.
- **Wireshark-style trace logging**: every arbitration round, delivery, CRC error, and
  dropped frame is logged with a timestamp to both the console and `can_trace.log`.

## Architecture

```
ECU Threads (Brake / Engine / Dashboard)
        |
   queue_message()  -->  pending_messages (per-sender TX buffer, dedup by ID)
        |
   process_bus()
        |
   bit-level arbitration  -->  winner + losers (re-queued for next round)
        |
   simulated transmission (chance of corruption)
        |
   CRC check  -->  OK: broadcast to other ECUs
              -->  mismatch: retransmit (up to 3x) or drop
        |
   CANLogger  -->  console + can_trace.log
```

## Running it

```bash
python3 main.py
```

Runs indefinitely, printing live bus activity. Press Ctrl+C to stop. Check
`can_trace.log` afterward for the full trace.

### Optional: bridge onto a real/virtual CAN interface (SocketCAN)

On a Linux machine (not inside a restricted sandbox/container), you can bridge
this simulator onto a real `vcan0` virtual CAN interface so standard Linux CAN
tooling (`candump`, `cansend`) can observe and inject traffic:

```bash
pip install python-can

sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0

python3 main.py --socketcan
```

Then in another terminal:

```bash
candump vcan0
```

You'll see every frame this simulator delivers appear on the real interface,
in standard CAN trace format, alongside this project's own console/log
output. You can also inject a frame manually from the other terminal and this
program will print it:

```bash
cansend vcan0 123#DEADBEEF
```

If `vcan0` isn't set up yet, `--socketcan` will print clear setup instructions
and fall back to pure simulation instead of crashing.

## Files

| File | Purpose |
|---|---|
| `message.py` | `CANMessage` class: frame structure, DLC, CRC-8 checksum, corruption/retransmit helpers |
| `can_bus.py` | `CANBus` class: message queueing, bit-level arbitration, CRC error handling |
| `ecu.py` | `ECU` class (a thread per node) + realistic signal generators (RPM, brake pressure, status) |
| `logger.py` | `CANLogger`: Wireshark-style console + file trace |
| `socketcan_bridge.py` | Optional bridge onto a real Linux SocketCAN interface via `python-can` |
| `main.py` | Wires up the bus and 3 ECUs; `--socketcan` flag enables the bridge |

## Known simplifications (vs. real CAN)

- Uses a custom CRC-8 (poly `0x07`) for clarity, not the real 15-bit CAN CRC polynomial.
- Doesn't implement bit stuffing, the full error-frame protocol, or bus-off state
  transitions for repeatedly faulty nodes.
- Runs as a logical simulation in Python threads rather than on a real/virtual CAN
  interface.

## Possible next steps

- Add a simple live dashboard (matplotlib or a small web UI) visualizing bus load and
  arbitration outcomes over time.
- Track error counters per ECU and simulate a bus-off state for a node that racks up
  too many CRC errors.
- Feed frames received from the SocketCAN listener back into the simulated ECUs
  instead of just printing them, so external tools can fully participate in the
  simulation.

## Requirements

- Python 3
- `python-can` (only needed for `--socketcan`): `pip install python-can`
- Linux with the `vcan` kernel module, for `--socketcan` only

## Technologies

- Python (threading, OOP)
- Automotive communication concepts: CAN 2.0A framing, bus arbitration, CRC error detection
