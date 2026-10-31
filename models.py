from dataclasses import dataclass, field
from typing import Optional, Tuple
import math


@dataclass
class Vehicle:
    vehicle_id: str
    x: float
    y: float
    speed: float
    acceleration: float
    heading: float
    lane: str = "lane_1"
    timestamp: float = 0.0
    tx_power_dbm: float = 23.0

    def step(self, dt: float):
        self.speed = max(0.0, self.speed + self.acceleration * dt)
        rad = math.radians(self.heading)
        self.x += self.speed * math.cos(rad) * dt
        self.y += self.speed * math.sin(rad) * dt


@dataclass
class Message:
    sender_id: str
    message_id: str
    sequence_number: int
    creation_time: float
    expiry_time: float
    priority: int = 0
    hop_count: int = 0
    payload_bytes: int = 200

    def key(self):
        return (self.sender_id, self.message_id, self.sequence_number)

    def copy_for_forward(self):
        data = self.__dict__.copy()
        data["hop_count"] = self.hop_count + 1
        return type(self)(**data)


@dataclass
class CAM(Message):
    x: float = 0.0
    y: float = 0.0
    speed: float = 0.0
    acceleration: float = 0.0
    heading: float = 0.0
    lane: str = "lane_1"

    @classmethod
    def from_vehicle(cls, vehicle, sequence, now, expiry=1.0):
        return cls(
            sender_id=vehicle.vehicle_id,
            message_id=f"CAM-{vehicle.vehicle_id}",
            sequence_number=sequence,
            creation_time=now,
            expiry_time=now + expiry,
            priority=0,
            x=vehicle.x,
            y=vehicle.y,
            speed=vehicle.speed,
            acceleration=vehicle.acceleration,
            heading=vehicle.heading,
            lane=vehicle.lane,
            payload_bytes=200,
        )

    def __str__(self):
        return (
            f"CAM(sender={self.sender_id}, pos=({self.x:.1f},{self.y:.1f}), "
            f"speed={self.speed:.1f}, acc={self.acceleration:.1f}, "
            f"seq={self.sequence_number}, hop={self.hop_count})"
        )


@dataclass
class DENM(Message):
    event_id: str = ""
    event_type: str = "HAZARD"
    severity: int = 1
    x: float = 0.0
    y: float = 0.0

    @classmethod
    def hazard(cls, vehicle, event_id, event_type, severity, now,
               duration=10.0, sequence=1):
        return cls(
            sender_id=vehicle.vehicle_id,
            message_id=f"DENM-{vehicle.vehicle_id}-{event_id}",
            sequence_number=sequence,
            creation_time=now,
            expiry_time=now + duration,
            priority=1,
            event_id=event_id,
            event_type=event_type,
            severity=max(1, min(5, severity)),
            x=vehicle.x,
            y=vehicle.y,
            payload_bytes=300,
        )

    def __str__(self):
        return (
            f"DENM(sender={self.sender_id}, event={self.event_id}, "
            f"type={self.event_type}, severity={self.severity}, "
            f"pos=({self.x:.1f},{self.y:.1f}), seq={self.sequence_number}, "
            f"hop={self.hop_count})"
        )
