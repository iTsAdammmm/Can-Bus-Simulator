from can_bus import CANBus
from ecu import ECU


bus = CANBus()

engine = ECU("Engine ECU", bus)
brake = ECU("Brake ECU", bus)
dashboard = ECU("Dashboard ECU", bus)

bus.connect(engine)
bus.connect(brake)
bus.connect(dashboard)

engine.start()
brake.start()
dashboard.start()

bus.start()