"""
JARVIS — Rooms API Router
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.core.security import get_current_user
from app.db.models import Room

router = APIRouter(prefix="/rooms", tags=["rooms"])


class RoomCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9_]+$")
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = ""
    icon: Optional[str] = "home"
    order: Optional[int] = 0


class RoomResponse(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    order: int
    created_at: datetime


@router.get("", response_model=list[RoomResponse])
async def list_rooms(
    request: Request,
    _user=Depends(get_current_user)
):
    """List all rooms."""
    db = request.app.state.db
    async with db.get_session() as session:
        result = await session.execute(select(Room).order_by(Room.order.asc()))
        rooms = result.scalars().all()
        return [
            RoomResponse(
                id=r.id,
                name=r.name,
                description=r.description or "",
                icon=r.icon or "home",
                order=r.order or 0,
                created_at=r.created_at
            )
            for r in rooms
        ]


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    data: RoomCreate,
    request: Request,
    _user=Depends(get_current_user)
):
    """Create a new room."""
    db = request.app.state.db
    async with db.get_session() as session:
        conflict = await session.execute(select(Room).where(Room.id == data.id))
        if conflict.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Room ID already exists")

        room = Room(
            id=data.id,
            name=data.name,
            description=data.description,
            icon=data.icon or "home",
            order=data.order or 0
        )
        session.add(room)
        await session.commit()
        await session.refresh(room)
        return RoomResponse(
            id=room.id,
            name=room.name,
            description=room.description or "",
            icon=room.icon or "home",
            order=room.order or 0,
            created_at=room.created_at
        )


@router.delete("/{id}")
async def delete_room(
    id: str,
    request: Request,
    _user=Depends(get_current_user)
):
    """Delete room."""
    db = request.app.state.db
    async with db.get_session() as session:
        result = await session.execute(select(Room).where(Room.id == id))
        room = result.scalar_one_or_none()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        await session.delete(room)
        await session.commit()
        return {"success": True}
