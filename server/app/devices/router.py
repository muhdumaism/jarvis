"""
JARVIS — Device API Router

REST API endpoints for device CRUD and control.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.security import get_current_user
from app.devices.schemas import (
    DeviceCreate, DeviceUpdate, DeviceResponse,
    DeviceControlRequest, DeviceControlResponse,
)

router = APIRouter(prefix="/devices", tags=["devices"])


def _get_device_manager(request: Request):
    return request.app.state.device_manager


@router.get("", response_model=list[DeviceResponse])
async def list_devices(
    device_manager=Depends(_get_device_manager),
    _user=Depends(get_current_user),
):
    """List all devices."""
    devices = await device_manager.get_all()
    return devices


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    data: DeviceCreate,
    device_manager=Depends(_get_device_manager),
    _user=Depends(get_current_user),
):
    """Create a new device."""
    if device_manager.device_exists(data.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device already exists: {data.id}",
        )
    device = await device_manager.create(data.model_dump())
    return device


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    device_manager=Depends(_get_device_manager),
    _user=Depends(get_current_user),
):
    """Get a device by ID."""
    device = await device_manager.get(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")
    return device


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: str,
    data: DeviceUpdate,
    device_manager=Depends(_get_device_manager),
    _user=Depends(get_current_user),
):
    """Update a device."""
    device = await device_manager.update(device_id, data.model_dump(exclude_unset=True))
    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")
    return device


@router.delete("/{device_id}")
async def delete_device(
    device_id: str,
    device_manager=Depends(_get_device_manager),
    _user=Depends(get_current_user),
):
    """Delete a device."""
    if not await device_manager.delete(device_id):
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")
    return {"success": True}


@router.post("/{device_id}/control", response_model=DeviceControlResponse)
async def control_device(
    device_id: str,
    data: DeviceControlRequest,
    device_manager=Depends(_get_device_manager),
    _user=Depends(get_current_user),
):
    """Send a control command to a device.
    
    Returns immediately with pending state. Actual state confirmation
    comes via WebSocket when the node ACKs.
    """
    try:
        result = await device_manager.execute_command(
            device_id=device_id,
            action=data.action,
            source=data.source,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{device_id}/state")
async def get_device_state(
    device_id: str,
    device_manager=Depends(_get_device_manager),
    _user=Depends(get_current_user),
):
    """Get current device state."""
    device = await device_manager.get(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")
    return {
        "device_id": device_id,
        "state": device["state"],
        "confirmed": device["confirmed"],
        "last_changed": device["last_changed"],
    }


@router.get("/{device_id}/history")
async def get_device_history(
    device_id: str,
    limit: int = 50,
    device_manager=Depends(_get_device_manager),
    _user=Depends(get_current_user),
):
    """Get device state change history."""
    if not device_manager.device_exists(device_id):
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")
    history = await device_manager.get_state_history(device_id, limit)
    return history
