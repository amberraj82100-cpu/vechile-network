from dataclasses import dataclass


@dataclass
class Metrics:
    tx: int = 0
    rx: int = 0
    lost: int = 0
    duplicates: int = 0
    ttl_drops: int = 0
    expired: int = 0
    forwards: int = 0
    generated: int = 0
    total_latency_ms: float = 0.0
    neighbors_sum: int = 0
    neighbor_samples: int = 0
    collision: int = 0
    total_attempts: int = 0
    channel_load_sum: float = 0.0
    channel_load_samples: int = 0

    def pdr(self):
        return self.rx / self.tx if self.tx else 0.0

    def avg_latency(self):
        return self.total_latency_ms / self.rx if self.rx else 0.0

    def duplicate_ratio(self):
        return self.duplicates / self.total_attempts if self.total_attempts else 0.0

    def avg_neighbors(self):
        return self.neighbors_sum / self.neighbor_samples if self.neighbor_samples else 0.0

    def channel_load(self):
        return self.channel_load_sum / self.channel_load_samples if self.channel_load_samples else 0.0

    def score(self):
        # A practical 0-100 research-bench score, not an academic metric.
        pdr = self.pdr()
        latency = self.avg_latency()
        collision_penalty = min(1.0, self.collision / max(1, self.tx))
        latency_score = max(0.0, 1.0 - min(latency / 200.0, 1.0))
        return 100.0 * (
            0.55 * pdr +
            0.25 * latency_score +
            0.20 * (1.0 - collision_penalty)
        )

    def as_dict(self):
        return {
            "PDR": round(self.pdr(), 4),
            "End-to-end delay (ms)": round(self.avg_latency(), 3),
            "Forwarding count": self.forwards,
            "Duplicate ratio": round(self.duplicate_ratio(), 4),
            "TTL drops": self.ttl_drops,
            "Expired messages": self.expired,
            "Average neighbors": round(self.avg_neighbors(), 3),
            "Channel load": round(self.channel_load(), 4),
            "Resource collisions": self.collision,
            "Research bench score": round(self.score(), 2),
        }
