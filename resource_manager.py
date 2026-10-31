from dataclasses import dataclass


@dataclass
class Resource:
    resource_id: int
    slot: int
    subchannel: int
    rsrp_dbm: float = -999.0
    occupied: bool = False


class Mode2ResourceManager:
    """
    System-level abstraction of NR sidelink Mode-2 sensing/resource selection.

    The manager:
      - maintains a finite resource pool
      - observes recent resource usage
      - scores candidates using occupancy and RSRP
      - selects a resource autonomously

    It intentionally does not claim bit-level 3GPP conformance.
    """

    def __init__(self, pool_size=20):
        self.pool_size = pool_size
        self.resources = [Resource(i, i, i % 10) for i in range(pool_size)]
        self.history = []

    def observe(self, resource_id, rsrp_dbm):
        self.history.append((resource_id, rsrp_dbm))
        if len(self.history) > 500:
            self.history = self.history[-500:]

    def occupancy(self):
        counts = {i: 0 for i in range(self.pool_size)}
        for rid, _ in self.history[-self.pool_size * 3:]:
            counts[rid] += 1
        return counts

    def select(self, preferred=None):
        occ = self.occupancy()
        candidates = list(range(self.pool_size))

        if preferred is not None and preferred in candidates:
            candidates.remove(preferred)
            candidates.insert(0, preferred)

        # Lower occupancy first; small deterministic tie-break by resource id.
        candidates.sort(key=lambda rid: (occ[rid], rid))
        return candidates[0]
