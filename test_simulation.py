import json
from models import Vehicle, DENM
from network import NRV2XSidelink


def build():
    with open("config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)

    net = NRV2XSidelink(cfg)
    positions = [0, 80, 160, 240, 320, 400]

    for i, x in enumerate(positions):
        net.register(Vehicle(
            vehicle_id=f"V{i+1}",
            x=x, y=0,
            speed=20,
            acceleration=0,
            heading=0
        ))

    return net


def run():
    net = build()
    source = net.vehicles["V1"]

    # Event-driven DENM
    net.sequence["V1"] += 1
    denm = DENM.hazard(
        source, "E0001", "ACCIDENT", 5,
        now=0.0, duration=20.0, sequence=1
    )

    net.broadcast("V1", denm)

    for _ in range(100):
        net.step(0.1)

    print("=" * 60)
    print("NR-V2X RESEARCH BENCH SCORECARD")
    print("=" * 60)

    for k, v in net.metrics.as_dict().items():
        print(f"{k:28} {v}")

    print("\nThis score is a project-specific composite indicator.")
    print("For publication, report the raw metrics and confidence intervals")
    print("rather than presenting this score as a standard metric.")


if __name__ == "__main__":
    run()
