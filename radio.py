from dataclasses import dataclass
import math
import random


@dataclass
class RadioResult:
    delivered: bool
    distance_m: float
    rsrp_dbm: float
    sinr_db: float
    mcs: str
    bler: float
    resource_id: int
    collision: bool
    propagation_delay_ms: float


class RadioModel:
    """
    System-level NR-V2X/PC5 abstraction.

    It models:
      distance -> path loss -> received power -> interference -> SINR
      -> MCS -> BLER -> packet outcome.

    It is NOT a 3GPP PHY implementation.
    """

    def __init__(self, cfg, rng=None):
        self.cfg = cfg
        self.rng = rng or random.Random()
        self.resource_users = {}

    def path_loss_db(self, distance_m):
        d = max(1.0, distance_m)
        # Tunable log-distance model around 1 m reference.
        f_ghz = self.cfg["carrier_frequency_ghz"]
        fspl_1m = 32.45 + 20 * math.log10(f_ghz)
        n = self.cfg["path_loss_exponent"]
        shadow = self.rng.gauss(0.0, self.cfg["shadowing_std_db"])
        return fspl_1m + 10 * n * math.log10(d) + shadow

    def rsrp(self, tx_power_dbm, distance_m):
        return tx_power_dbm - self.path_loss_db(distance_m)

    def choose_mcs(self, sinr_db):
        thresholds = self.cfg["sinr_thresholds_db"]
        if sinr_db >= thresholds["256QAM"]:
            return "256QAM"
        if sinr_db >= thresholds["64QAM"]:
            return "64QAM"
        if sinr_db >= thresholds["16QAM"]:
            return "16QAM"
        if sinr_db >= thresholds["QPSK"]:
            return "QPSK"
        return "OUTAGE"

    def estimate_bler(self, mcs, sinr_db):
        if mcs == "OUTAGE":
            return 1.0
        base = self.cfg["bler"][mcs]
        thresholds = self.cfg["sinr_thresholds_db"]
        margin = sinr_db - thresholds[mcs]
        # Smoothly improves as SINR rises above threshold.
        return max(0.0001, min(1.0, base * math.exp(-0.22 * margin)))

    def evaluate(self, sender, receiver, message, all_vehicles, resource_id):
        dx = sender.x - receiver.x
        dy = sender.y - receiver.y
        distance = math.hypot(dx, dy)

        rsrp = self.rsrp(sender.tx_power_dbm, distance)

        interference_mw = 10 ** (self.cfg["noise_floor_dbm"] / 10)
        interferers = 0
        radius = self.cfg["interference_radius_m"]

        for v in all_vehicles:
            if v.vehicle_id in (sender.vehicle_id, receiver.vehicle_id):
                continue
            d = math.hypot(v.x - receiver.x, v.y - receiver.y)
            if d <= radius:
                p = self.rsrp(v.tx_power_dbm, d)
                interference_mw += 10 ** (p / 10)
                interferers += 1

        signal_mw = 10 ** (rsrp / 10)
        sinr = 10 * math.log10(signal_mw / interference_mw)

        mcs = self.choose_mcs(sinr)
        bler = self.estimate_bler(mcs, sinr)

        collision = self.resource_users.get(resource_id, 0) > 1
        if collision:
            bler = min(1.0, bler + 0.55)

        delivered = distance <= self.cfg["communication_range_m"] if "communication_range_m" in self.cfg else True
        delivered = delivered and (self.rng.random() >= bler)

        c = 299_792_458.0
        delay_ms = (distance / c) * 1000.0

        return RadioResult(
            delivered=delivered,
            distance_m=distance,
            rsrp_dbm=rsrp,
            sinr_db=sinr,
            mcs=mcs,
            bler=bler,
            resource_id=resource_id,
            collision=collision,
            propagation_delay_ms=delay_ms,
        )
