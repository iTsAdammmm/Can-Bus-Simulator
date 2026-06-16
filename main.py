from can_bus import CANBus
from ecu import ECU
from message import CANMessage

bus = CANBus()

engine = ECU("Engine ECU")
brake = ECU("Brake ECU")
dashboard = ECU("Dashboard ECU")

bus.connect(engine)
bus.connect(brake)
bus.connect(dashboard)

message = CANMessage(100, "Engine ECU", "Speed=80")

bus.transmit(message)