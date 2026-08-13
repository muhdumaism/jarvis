"""
JARVIS — Scene API Router
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user
from app.db.models import Scene, SceneAction
from app.scenes.schemas import SceneCreate, SceneUpdate, SceneResponse, SceneActionResponse

router = APIRouter(prefix="/scenes", tags=["scenes"])


def _get_scene_manager(request: Request):
    return request.app.state.scene_manager


def _format_scene_response(scene: Scene) -> SceneResponse:
    actions = [
        SceneActionResponse(
            id=a.id,
            order=a.order,
            action_type=a.action_type,
            target=a.target,
            action=a.action,
            parameters=a.parameters or {}
        )
        for a in scene.actions
    ]
    return SceneResponse(
        id=scene.id,
        name=scene.name,
        description=scene.description or "",
        icon=scene.icon or "layers",
        actions=actions,
        created_at=scene.created_at,
        updated_at=scene.updated_at
    )


@router.get("", response_model=list[SceneResponse])
async def list_scenes(
    manager=Depends(_get_scene_manager),
    _user=Depends(get_current_user)
):
    """List all scenes."""
    async with manager.db.get_session() as session:
        result = await session.execute(
            select(Scene).options(selectinload(Scene.actions))
        )
        scenes = result.scalars().all()
        return [_format_scene_response(s) for s in scenes]


@router.post("", response_model=SceneResponse, status_code=status.HTTP_201_CREATED)
async def create_scene(
    data: SceneCreate,
    manager=Depends(_get_scene_manager),
    _user=Depends(get_current_user)
):
    """Create a new scene with sequential actions."""
    async with manager.db.get_session() as session:
        # Check name conflict
        conflict = await session.execute(
            select(Scene).where(Scene.name == data.name)
        )
        if conflict.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Scene name already exists")

        scene = Scene(
            name=data.name,
            description=data.description,
            icon=data.icon or "layers"
        )
        session.add(scene)
        await session.flush()  # Get ID

        for a in data.actions:
            action = SceneAction(
                scene_id=scene.id,
                order=a.order,
                action_type=a.action_type,
                target=a.target,
                action=a.action,
                parameters=a.parameters
            )
            session.add(action)

        await session.commit()
        
        # Load fully populated object
        result = await session.execute(
            select(Scene).options(selectinload(Scene.actions)).where(Scene.id == scene.id)
        )
        scene = result.scalar_one()
        return _format_scene_response(scene)


@router.get("/{id}", response_model=SceneResponse)
async def get_scene(
    id: int,
    manager=Depends(_get_scene_manager),
    _user=Depends(get_current_user)
):
    """Get single scene configuration details."""
    async with manager.db.get_session() as session:
        result = await session.execute(
            select(Scene).options(selectinload(Scene.actions)).where(Scene.id == id)
        )
        scene = result.scalar_one_or_none()
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")
        return _format_scene_response(scene)


@router.put("/{id}", response_model=SceneResponse)
async def update_scene(
    id: int,
    data: SceneUpdate,
    manager=Depends(_get_scene_manager),
    _user=Depends(get_current_user)
):
    """Update scene configuration and action steps."""
    async with manager.db.get_session() as session:
        result = await session.execute(
            select(Scene).options(selectinload(Scene.actions)).where(Scene.id == id)
        )
        scene = result.scalar_one_or_none()
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")

        if data.name:
            scene.name = data.name
        if data.description is not None:
            scene.description = data.description
        if data.icon:
            scene.icon = data.icon

        if data.actions is not None:
            # Delete old actions first
            for action in scene.actions:
                await session.delete(action)
            await session.flush()

            # Insert new actions
            for a in data.actions:
                action = SceneAction(
                    scene_id=scene.id,
                    order=a.order,
                    action_type=a.action_type,
                    target=a.target,
                    action=a.action,
                    parameters=a.parameters
                )
                session.add(action)

        await session.commit()
        
        # Reload
        result = await session.execute(
            select(Scene).options(selectinload(Scene.actions)).where(Scene.id == id)
        )
        scene = result.scalar_one()
        return _format_scene_response(scene)


@router.delete("/{id}")
async def delete_scene(
    id: int,
    manager=Depends(_get_scene_manager),
    _user=Depends(get_current_user)
):
    """Delete scene configuration."""
    async with manager.db.get_session() as session:
        result = await session.execute(
            select(Scene).where(Scene.id == id)
        )
        scene = result.scalar_one_or_none()
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")
        
        await session.delete(scene)
        await session.commit()
        return {"success": True}


@router.post("/{id}/activate")
async def activate_scene(
    id: int,
    manager=Depends(_get_scene_manager),
    _user=Depends(get_current_user)
):
    """Trigger/activate a scene's actions sequence."""
    success = await manager.execute_scene(id)
    if not success:
        raise HTTPException(status_code=400, detail="Scene activation failed")
    return {"success": True}
