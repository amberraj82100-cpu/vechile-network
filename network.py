import math
import random
from collections import defaultdict
from models import Vehicle, CAM, DENM
from radio import RadioModel
from resource_manager import Mode2ResourceManager
from dissemination import DisseminationManager
from metrics import Metrics


class NRV2XSidelink:
    """
    Integrated system-level NR-V2X/PC5 simulator.

    Application messages are sent through an NR sidelink abstraction rather
    than a simple distance-only queue.
    """

    def __init__(self, config):
        self.cfg = config
        self.rng = random.Random(config["simulation"]["random_seed"])
        radio_cfg = dict(config["radio"])
        radio_cfg["communication_range_m"] = config["simulation"]["communication_range_m"]

        self.radio = RadioModel(radio_cfg, self.rng)
        self.resource = Mode2ResourceManager(radio_cfg["resource_pool_size"])
        self.vehicles = {}
        self.queues = defaultdict(list)
        self.dissemination = {}
        self.sequence = defaultdict(int)
        self.metrics = Metrics()
        self.now = 0.0
        self.last_radio_events = []

    def register(self, vehicle):
        self.vehicles[vehicle.vehicle_id] = vehicle
        self.dissemination[vehicle.vehicle_id] = DisseminationManager(
            max_ttl=self.cfg["dissemination"]["max_ttl"],
            duplicate_filtering=self.cfg["dissemination"]["duplicate_filtering"],
            forwarding=self.cfg["dissemination"]["forwarding"],
        )

    def distance(self, a, b):
        return math.hypot(a.x - b.x, a.y - b.y)

    def neighbors(self, vehicle_id):
        if vehicle_id not in self.vehicles:
            return []
        v = self.vehicles[vehicle_id]
        return [
            other.vehicle_id for other in self.vehicles.values()
            if other.vehicle_id != vehicle_id
            and self.distance(v, other) <= self.cfg["simulation"]["communication_range_m"]
        ]

    def _resource_for(self, sender_id):
        return self.resource.select()

    def transmit(self, sender_id, receiver_id, message):
        if sender_id not in self.vehicles or receiver_id not in self.vehicles:
            return False

        sender = self.vehicles[sender_id]
        receiver = self.vehicles[receiver_id]

        if receiver_id not in self.neighbors(sender_id):
            return False

        rid = self._resource_for(sender_id)
        self.resource.observe(rid, -90.0)
        self.metrics.tx += 1
        self.metrics.total_attempts += 1

        result = self.radio.evaluate(
            sender, receiver, message,
            list(self.vehicles.values()), rid
        )

        self.last_radio_events.append((sender_id, receiver_id, message, result))
        self.metrics.channel_load_sum += min(1.0, len(self.vehicles) / max(1, self.resource.pool_size))
        self.metrics.channel_load_samples += 1

        if result.collision:
            self.metrics.collision += 1

        if result.delivered:
            self.queues[receiver_id].append((message, self.now + result.propagation_delay_ms / 1000.0))
            return True

        self.metrics.lost += 1
        return False

    def broadcast(self, sender_id, message, exclude=None):
        delivered = 0
        for rid in self.neighbors(sender_id):
            if exclude is not None and rid == exclude:
                continue
            if self.transmit(sender_id, rid, message):
                delivered += 1
        return delivered

    def receive(self, vehicle_id):
        if vehicle_id not in self.vehicles:
            return []

        now = self.vehicles[vehicle_id].timestamp
        out = []
        queue = self.queues[vehicle_id]
        self.queues[vehicle_id] = []

        manager = self.dissemination[vehicle_id]

        for message, arrival_time in queue:
            if arrival_time > now:
                self.queues[vehicle_id].append((message, arrival_time))
                continue

            ok, reason = manager.valid(message, now)
            if not ok:
                if reason == "duplicate":
                    self.metrics.duplicates += 1
                elif reason == "ttl":
                    self.metrics.ttl_drops += 1
                elif reason == "expired":
                    self.metrics.expired += 1
                continue

            manager.mark_seen(message)
            self.metrics.rx += 1
            self.metrics.total_latency_ms += max(
                0.0, (now - message.creation_time) * 1000.0
            )
            out.append(message)

        return out

    def forward(self, vehicle_id, message):
        manager = self.dissemination[vehicle_id]
        if not manager.should_forward(message, self.vehicles[vehicle_id].timestamp):
            return 0

        forwarded = manager.prepare_forward(message)
        self.metrics.forwards += 1
        return self.broadcast(vehicle_id, forwarded, exclude=message.sender_id)

    def generate_cam(self, vehicle_id):
        vehicle = self.vehicles[vehicle_id]
        self.sequence[vehicle_id] += 1
        cam = CAM.from_vehicle(
            vehicle,
            self.sequence[vehicle_id],
            vehicle.timestamp,
            expiry=1.0
        )
        return self.broadcast(vehicle_id, cam)

    def generate_denm(self, vehicle_id, event_type="ACCIDENT", severity=3):
        vehicle = self.vehicles[vehicle_id]
        self.sequence[vehicle_id] += 1
        denm = DENM.hazard(
            vehicle,
            event_id=f"E{self.sequence[vehicle_id]:04d}",
            event_type=event_type,
            severity=severity,
            now=vehicle.timestamp,
            duration=10.0,
            sequence=self.sequence[vehicle_id],
        )
        return self.broadcast(vehicle_id, denm)

    def step(self, dt):
        self.now += dt

        for v in self.vehicles.values():
            v.timestamp = self.now
            v.step(dt)

        self.last_radio_events = []

        for vehicle_id in list(self.vehicles):
            self.metrics.neighbors_sum += len(self.neighbors(vehicle_id))
            self.metrics.neighbor_samples += 1

        # Forward received messages once per simulation tick.
        for vehicle_id in list(self.vehicles):
            received = self.receive(vehicle_id)
            for message in received:
                if isinstance(message, DENM):
                    self.forward(vehicle_id, message)

        return self.last_radio_events
