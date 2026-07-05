import argparse
import threading

from can_bus import CANBus
from ecu import ECU, rpm_data, brake_pressure_data, dashboard_status_data

# Realistic-ish CAN ID map (lower ID = higher priority on the bus).
# Braking is safety-critical, so it gets the lowest ID and will win
# arbitration against the engine/dashboard whenever they collide.
BRAKE_ID = 0x100
ENGINE_ID = 0x200
DASHBOARD_ID = 0x300


def print_external_frame(frame):
    print(f"[SocketCAN <- vcan0] ID=0x{frame.arbitration_id:03X} Data={list(frame.data)}")


def main():
    parser = argparse.ArgumentParser(description="CAN Bus Communication Simulator")
    parser.add_argument(
        "--socketcan",
        action="store_true",
        help="Mirror delivered frames onto a real/virtual CAN interface (vcan0) "
             "via python-can, and print any frames injected from outside "
             "(e.g. `cansend vcan0 123#DEADBEEF`). Requires vcan0 to already "
             "exist (see README) -- this will NOT work in a plain sandbox.",
    )
    args = parser.parse_args()

    bridge = None
    if args.socketcan:
        from socketcan_bridge import SocketCANBridge
        try:
            bridge = SocketCANBridge()
        except OSError as e:
            print(
                f"[SocketCAN] could not open 'vcan0': {e}\n"
                "Make sure the virtual CAN interface exists first:\n"
                "  sudo modprobe vcan\n"
                "  sudo ip link add dev vcan0 type vcan\n"
                "  sudo ip link set up vcan0\n"
                "Falling back to pure simulation (no SocketCAN bridge)."
            )
            bridge = None
        else:
            listener_thread = threading.Thread(
                target=bridge.listen, args=(print_external_frame,), daemon=True
            )
            listener_thread.start()
            print("[SocketCAN] bridged to vcan0 -- run `candump vcan0` in another terminal to watch.")

    bus = CANBus(socketcan_bridge=bridge)

    brake = ECU("Brake ECU", BRAKE_ID, bus, brake_pressure_data, period_range=(1, 2))
    engine = ECU("Engine ECU", ENGINE_ID, bus, rpm_data, period_range=(1, 2))
    dashboard = ECU("Dashboard ECU", DASHBOARD_ID, bus, dashboard_status_data, period_range=(2, 3))

    for ecu in (brake, engine, dashboard):
        bus.connect(ecu)
        ecu.start()

    bus.start()


if __name__ == "__main__":
    main()