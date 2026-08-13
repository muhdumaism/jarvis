"""
JARVIS — Automation API Router
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select

from app.core.security import get_current_user
from app.db.models import Automation
from app.automation.schemas import AutomationCreate, AutomationUpdate, AutomationResponse

router = APIRouter(prefix="/automations", tags=["automations"])


def _get_automation_engine(request: Request):
    return request.app.state.automation_engine


@router.get("", response_model=list[AutomationResponse])
async def list_automations(
    engine=Depends(_get_automation_engine),
    _user=Depends(get_current_user),
):
    """List all automations."""
    async with engine.db.get_session() as session:
        result = await session.execute(select(Automation))
        autos = result.scalars().all()
        
        # Format response
        response = []
        for a in autos:
            response.append(AutomationResponse(
                id=a.id,
                name=a.name,
                description=a.description or "",
                enabled=a.enabled,
                trigger_type=a.trigger_type,
                trigger_config=a.trigger_config,
                conditions=a.conditions or [],
                actions=a.actions,
                cooldown_seconds=a.cooldown_seconds,
                last_triggered=a.last_triggered,
                trigger_count=a.trigger_count,
                created_at=a.created_at,
                updated_at=a.updated_at
            ))
        return response


@router.post("", response_model=AutomationResponse, status_code=status.HTTP_201_CREATED)
async def create_automation(
    data: AutomationCreate,
    engine=Depends(_get_automation_engine),
    _user=Depends(get_current_user),
):
    """Create a new automation rule."""
    async with engine.db.get_session() as session:
        auto = Automation(
            name=data.name,
            description=data.description,
            enabled=data.enabled,
            trigger_type=data.trigger_type,
            trigger_config=data.trigger_config,
            conditions=data.conditions,
            actions=data.actions,
            cooldown_seconds=data.cooldown_seconds
        )
        session.add(auto)
        await session.commit()
        await session.refresh(auto)

        # Reload engine cache
        await engine.load_automations()

        return AutomationResponse(
            id=auto.id,
            name=auto.name,
            description=auto.description or "",
            enabled=auto.enabled,
            trigger_type=auto.trigger_type,
            trigger_config=auto.trigger_config,
            conditions=auto.conditions or [],
            actions=auto.actions,
            cooldown_seconds=auto.cooldown_seconds,
            last_triggered=auto.last_triggered,
            trigger_count=auto.trigger_count,
            created_at=auto.created_at,
            updated_at=auto.updated_at
        )


@router.get("/{id}", response_model=AutomationResponse)
async def get_automation(
    id: int,
    engine=Depends(_get_automation_engine),
    _user=Depends(get_current_user),
):
    """Get single automation details."""
    async with engine.db.get_session() as session:
        result = await session.execute(
            select(Automation).where(Automation.id == id)
        )
        a = result.scalar_one_or_none()
        if not a:
            raise HTTPException(status_code=404, detail="Automation not found")
        
        return AutomationResponse(
            id=a.id,
            name=a.name,
            description=a.description or "",
            enabled=a.enabled,
            trigger_type=a.trigger_type,
            trigger_config=a.trigger_config,
            conditions=a.conditions or [],
            actions=a.actions,
            cooldown_seconds=a.cooldown_seconds,
            last_triggered=a.last_triggered,
            trigger_count=a.trigger_count,
            created_at=a.created_at,
            updated_at=a.updated_at
        )


@router.put("/{id}", response_model=AutomationResponse)
async def update_automation(
    id: int,
    data: AutomationUpdate,
    engine=Depends(_get_automation_engine),
    _user=Depends(get_current_user),
):
    """Update automation details."""
    async with engine.db.get_session() as session:
        result = await session.execute(
            select(Automation).where(Automation.id == id)
        )
        auto = result.scalar_one_or_none()
        if not auto:
            raise HTTPException(status_code=404, detail="Automation not found")
        
        # Apply updates
        update_dict = data.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(auto, k, v)
        
        await session.commit()
        await session.refresh(auto)
        
        # Reload cache
        await engine.load_automations()

        return AutomationResponse(
            id=auto.id,
            name=auto.name,
            description=auto.description or "",
            enabled=auto.enabled,
            trigger_type=auto.trigger_type,
            trigger_config=auto.trigger_config,
            conditions=auto.conditions or [],
            actions=auto.actions,
            cooldown_seconds=auto.cooldown_seconds,
            last_triggered=auto.last_triggered,
            trigger_count=auto.trigger_count,
            created_at=auto.created_at,
            updated_at=auto.updated_at
        )


@router.delete("/{id}")
async def delete_automation(
    id: int,
    engine=Depends(_get_automation_engine),
    _user=Depends(get_current_user),
):
    """Delete automation."""
    async with engine.db.get_session() as session:
        result = await session.execute(
            select(Automation).where(Automation.id == id)
        )
        auto = result.scalar_one_or_none()
        if not auto:
            raise HTTPException(status_code=404, detail="Automation not found")
        
        await session.delete(auto)
        await session.commit()
        
        # Reload cache
        await engine.load_automations()
        return {"success": True}


@router.post("/{id}/test")
async def test_automation(
    id: int,
    engine=Depends(_get_automation_engine),
    _user=Depends(get_current_user),
):
    """Manually trigger automation for testing purposes."""
    success = await engine.trigger_automation(id, trigger_data={"test": True})
    return {"success": success}
