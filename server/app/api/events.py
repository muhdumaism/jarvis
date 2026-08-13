"""
JARVIS — Events Log API Router
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.core.security import get_current_user
from app.db.models import Event

router = APIRouter(prefix="/events", tags=["events"])


class EventResponse(BaseModel):
    id: int
    timestamp: datetime
    severity: str
    component: str
    event_type: str
    message: str
    message_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


@router.get("", response_model=list[EventResponse])
async def list_events(
    request: Request,
    component: Optional[str] = None,
    severity: Optional[str] = None,
    message_id: Optional[str] = None,
    limit: int = 100,
    _user=Depends(get_current_user)
):
    """Retrieve filtered, historical system events log from database."""
    db = request.app.state.db
    async with db.get_session() as session:
        query = select(Event).order_by(Event.timestamp.desc())

        if component:
            query = query.where(Event.component == component)
        if severity:
            query = query.where(Event.severity == severity)
        if message_id:
            query = query.where(Event.message_id == message_id)

        query = query.limit(limit)
        
        result = await session.execute(query)
        events = result.scalars().all()

        return [
            EventResponse(
                id=e.id,
                timestamp=e.timestamp,
                severity=e.severity,
                component=e.component,
                event_type=e.event_type,
                message=e.message,
                message_id=e.message_id,
                payload=e.payload
            )
            for e in events
        ]
