"""
JARVIS — Node API Router
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.core.security import get_current_user
from app.nodes.schemas import NodeCreate, NodeUpdate, NodeResponse

router = APIRouter(prefix="/nodes", tags=["nodes"])


def _get_node_manager(request: Request):
    return request.app.state.node_manager


@router.get("", response_model=list[NodeResponse])
async def list_nodes(
    node_manager=Depends(_get_node_manager),
    _user=Depends(get_current_user),
):
    return await node_manager.get_all()


@router.post("", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
async def create_node(
    data: NodeCreate,
    node_manager=Depends(_get_node_manager),
    _user=Depends(get_current_user),
):
    existing = await node_manager.get(data.id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Node already exists: {data.id}")
    return await node_manager.create(data.model_dump())


@router.get("/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: str,
    node_manager=Depends(_get_node_manager),
    _user=Depends(get_current_user),
):
    node = await node_manager.get(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node not found: {node_id}")
    return node


@router.put("/{node_id}", response_model=NodeResponse)
async def update_node(
    node_id: str,
    data: NodeUpdate,
    node_manager=Depends(_get_node_manager),
    _user=Depends(get_current_user),
):
    node = await node_manager.update(node_id, data.model_dump(exclude_unset=True))
    if not node:
        raise HTTPException(status_code=404, detail=f"Node not found: {node_id}")
    return node


@router.delete("/{node_id}")
async def delete_node(
    node_id: str,
    node_manager=Depends(_get_node_manager),
    _user=Depends(get_current_user),
):
    if not await node_manager.delete(node_id):
        raise HTTPException(status_code=404, detail=f"Node not found: {node_id}")
    return {"success": True}
