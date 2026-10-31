"""
Optional SUMO/TraCI adapter.

Install SUMO separately and:
    pip install traci

Then use:
    adapter = SumoAdapter("your.sumocfg")
    adapter.connect()
    adapter.sync(network)
"""


class SumoAdapter:
    def __init__(self, sumocfg, gui=True):
        self.sumocfg = sumocfg
        self.gui = gui
        self.traci = None

    def connect(self):
        import traci
        self.traci = traci
        binary = "sumo-gui" if self.gui else "sumo"
        self.traci.start([binary, "-c", self.sumocfg])

    def sync(self, network):
        if self.traci is None:
            raise RuntimeError("Call connect() first")

        from models import Vehicle

        ids = self.traci.vehicle.getIDList()

        for vid in ids:
            x, y = self.traci.vehicle.getPosition(vid)
            speed = self.traci.vehicle.getSpeed(vid)
            accel = self.traci.vehicle.getAcceleration(vid)
            angle = self.traci.vehicle.getAngle(vid)
            lane = self.traci.vehicle.getLaneID(vid)

            if vid not in network.vehicles:
                network.register(Vehicle(
                    vehicle_id=vid,
                    x=x, y=y, speed=speed,
                    acceleration=accel,
                    heading=90.0 - angle,
                    lane=lane
                ))
            else:
                v = network.vehicles[vid]
                v.x, v.y = x, y
                v.speed = speed
                v.acceleration = accel
                v.heading = 90.0 - angle
                v.lane = lane

    def step(self, dt=0.1):
        self.traci.simulationStep()

    def close(self):
        if self.traci:
            self.traci.close()
