from can_bus import CANBus
from ecu import ECU, rpm_data, brake_pressure_data, dashboard_status_data

# Realistic-ish CAN ID map (lower ID = higher priority on the bus).
# Braking is safety-critical, so it gets the lowest ID and will win
# arbitration against the engine/dashboard whenever they collide.
BRAKE_ID = 0x100
ENGINE_ID = 0x200
DASHBOARD_ID = 0x300


def main():
    bus = CANBus()

    brake = ECU("Brake ECU", BRAKE_ID, bus, brake_pressure_data, period_range=(1, 2))
    engine = ECU("Engine ECU", ENGINE_ID, bus, rpm_data, period_range=(1, 2))
    dashboard = ECU("Dashboard ECU", DASHBOARD_ID, bus, dashboard_status_data, period_range=(2, 3))

    for ecu in (brake, engine, dashboard):
        bus.connect(ecu)
        ecu.start()

    bus.start()


if __name__ == "__main__":
    main()