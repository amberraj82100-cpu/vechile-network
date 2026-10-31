import json
from models import Vehicle
from network import NRV2XSidelink


def main():
    with open("config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)

    net = NRV2XSidelink(cfg)

    for i in range(5):
        net.register(Vehicle(
            vehicle_id=f"V{i+1}",
            x=100 + i * 80,
            y=100,
            speed=18 + i,
            acceleration=0,
            heading=0
        ))

    for _ in range(300):
        net.step(0.1)

    print(net.metrics.as_dict())


if __name__ == "__main__":
    main()
