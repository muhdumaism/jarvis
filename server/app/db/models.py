"""
JARVIS Database Models — SQLAlchemy ORM

All 11 tables as defined in PROTOCOL.md and ARCHITECTURE.md.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime,
    ForeignKey, JSON, Index, Enum as SAEnum
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func
import enum


class Base(DeclarativeBase):
    """Base class for all JARVIS models."""
    pass


# ============================================================
# Enums
# ============================================================

class DeviceType(str, enum.Enum):
    RELAY = "relay"
    SENSOR = "sensor"
    SWITCH = "switch"
    DIMMER = "dimmer"


class DeviceState(str, enum.Enum):
    ON = "on"
    OFF = "off"
    UNKNOWN = "unknown"


class NodeStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class TriggerType(str, enum.Enum):
    TIME = "time"
    TEMPERATURE = "temperature"
    DEVICE_STATE = "device_state"
    SENSOR = "sensor"


class EventSeverity(str, enum.Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================
# Models
# ============================================================

class Room(Base):
    __tablename__ = "rooms"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, default="")
    icon = Column(String(32), default="home")
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    devices = relationship("Device", back_populates="room", cascade="all, delete-orphan")
    nodes = relationship("Node", back_populates="room", cascade="all, delete-orphan")


class Node(Base):
    __tablename__ = "nodes"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    room_id = Column(String(64), ForeignKey("rooms.id"), nullable=False)
    mac_address = Column(String(17), unique=True, nullable=True)  # AA:BB:CC:DD:EE:FF
    chip_type = Column(String(16), default="esp32")  # esp32, esp32s3
    firmware_version = Column(String(16), default="0.0.0")
    status = Column(String(16), default=NodeStatus.UNKNOWN.value)
    last_seen = Column(DateTime, nullable=True)
    uptime = Column(Integer, default=0)
    free_heap = Column(Integer, default=0)
    config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    room = relationship("Room", back_populates="nodes")
    devices = relationship("Device", back_populates="node", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_nodes_room_id", "room_id"),
        Index("ix_nodes_status", "status"),
    )


class Device(Base):
    __tablename__ = "devices"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    room_id = Column(String(64), ForeignKey("rooms.id"), nullable=False)
    node_id = Column(String(64), ForeignKey("nodes.id"), nullable=False)
    type = Column(String(16), default=DeviceType.RELAY.value)
    channel = Column(Integer, default=0)  # Relay channel on the node
    capabilities = Column(JSON, default=list)  # ["on", "off", "toggle"]
    state = Column(String(16), default=DeviceState.UNKNOWN.value)
    confirmed = Column(Boolean, default=False)
    last_changed = Column(DateTime, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    room = relationship("Room", back_populates="devices")
    node = relationship("Node", back_populates="devices")
    state_history = relationship("DeviceStateLog", back_populates="device", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_devices_room_id", "room_id"),
        Index("ix_devices_node_id", "node_id"),
    )


class DeviceStateLog(Base):
    """Historical log of device state changes."""
    __tablename__ = "device_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(64), ForeignKey("devices.id"), nullable=False)
    state = Column(String(16), nullable=False)
    confirmed = Column(Boolean, default=False)
    source = Column(String(32), default="unknown")  # voice, dashboard, automation, scene
    message_id = Column(String(64), nullable=True)  # Correlation ID
    changed_at = Column(DateTime, default=func.now())

    # Relationships
    device = relationship("Device", back_populates="state_history")

    __table_args__ = (
        Index("ix_device_states_device_id", "device_id"),
        Index("ix_device_states_changed_at", "changed_at"),
    )


class Event(Base):
    """System event log for observability."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now())
    severity = Column(String(16), default=EventSeverity.INFO.value)
    component = Column(String(32), nullable=False)  # voice, device, node, music, etc.
    event_type = Column(String(64), nullable=False)
    message = Column(Text, nullable=False)
    message_id = Column(String(64), nullable=True)  # Correlation ID
    payload = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_events_timestamp", "timestamp"),
        Index("ix_events_component", "component"),
        Index("ix_events_severity", "severity"),
        Index("ix_events_message_id", "message_id"),
    )


class Automation(Base):
    __tablename__ = "automations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, default="")
    enabled = Column(Boolean, default=True)
    trigger_type = Column(String(16), nullable=False)  # time, temperature, device_state, sensor
    trigger_config = Column(JSON, nullable=False)
    # Examples:
    # time: {"cron": "0 23 * * *"} or {"time": "23:00"}
    # temperature: {"sensor_id": "...", "operator": ">", "value": 28}
    # device_state: {"device_id": "...", "state": "on"}
    conditions = Column(JSON, default=list)  # Additional conditions
    actions = Column(JSON, nullable=False)
    # Example: [{"device_id": "room_fan", "action": "turn_on"}]
    cooldown_seconds = Column(Integer, default=30)
    last_triggered = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    runs = relationship("AutomationRun", back_populates="automation", cascade="all, delete-orphan")


class AutomationRun(Base):
    __tablename__ = "automation_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    automation_id = Column(Integer, ForeignKey("automations.id"), nullable=False)
    triggered_at = Column(DateTime, default=func.now())
    trigger_data = Column(JSON, nullable=True)
    actions_executed = Column(JSON, nullable=True)
    success = Column(Boolean, default=True)
    error = Column(Text, nullable=True)

    # Relationships
    automation = relationship("Automation", back_populates="runs")

    __table_args__ = (
        Index("ix_automation_runs_automation_id", "automation_id"),
        Index("ix_automation_runs_triggered_at", "triggered_at"),
    )


class Scene(Base):
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False, unique=True)
    description = Column(Text, default="")
    icon = Column(String(32), default="layers")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    actions = relationship("SceneAction", back_populates="scene", cascade="all, delete-orphan")


class SceneAction(Base):
    __tablename__ = "scene_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scene_id = Column(Integer, ForeignKey("scenes.id"), nullable=False)
    order = Column(Integer, default=0)
    action_type = Column(String(32), nullable=False)  # device_control, music_control, delay
    target = Column(String(64), nullable=True)  # device_id or music
    action = Column(String(32), nullable=False)  # turn_on, turn_off, play, pause
    parameters = Column(JSON, default=dict)

    # Relationships
    scene = relationship("Scene", back_populates="actions")

    __table_args__ = (
        Index("ix_scene_actions_scene_id", "scene_id"),
    )


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(128), primary_key=True)
    value = Column(Text, nullable=True)
    type = Column(String(16), default="string")  # string, int, float, bool, json
    description = Column(Text, default="")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class FirmwareVersion(Base):
    __tablename__ = "firmware_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(16), nullable=False)
    chip_type = Column(String(16), nullable=False)  # esp32, esp32s3
    target = Column(String(16), nullable=False)  # main, node
    filename = Column(String(256), nullable=False)
    file_size = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False)
    description = Column(Text, default="")
    uploaded_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index("ix_firmware_chip_type", "chip_type"),
        Index("ix_firmware_target", "target"),
    )
