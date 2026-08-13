"""
JARVIS — Settings and Database Backup Router
"""

import tempfile
import os
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any

from app.core.security import require_admin
from app.db.models import Setting

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingUpdate(BaseModel):
    value: str


@router.get("")
async def get_settings(
    request: Request,
    _admin=Depends(require_admin)
):
    """Retrieve all system settings from database."""
    db = request.app.state.db
    async with db.get_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(Setting))
        settings_list = result.scalars().all()
        return {s.key: s.value for s in settings_list}


@router.put("/{key}")
async def update_setting(
    key: str,
    data: SettingUpdate,
    request: Request,
    _admin=Depends(require_admin)
):
    """Update a system setting value."""
    db = request.app.state.db
    async with db.get_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(Setting).where(Setting.key == key))
        setting = result.scalar_one_or_none()
        if not setting:
            setting = Setting(key=key, value=data.value, type="string")
            session.add(setting)
        else:
            setting.value = data.value
        await session.commit()
        return {"key": key, "value": setting.value}


@router.post("/backup")
async def create_backup(
    request: Request,
    _admin=Depends(require_admin)
):
    """Trigger a database file backup and download the .db file."""
    db = request.app.state.db
    try:
        backup_path = await db.backup()
        return FileResponse(
            backup_path,
            media_type="application/octet-stream",
            filename=os.path.basename(backup_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup execution failed: {e}")


@router.post("/restore")
async def restore_backup(
    request: Request,
    file: UploadFile = File(...),
    _admin=Depends(require_admin)
):
    """Restore database file from uploaded backup file."""
    if not file.filename.endswith(".db"):
        raise HTTPException(status_code=400, detail="Invalid backup file type. Must be .db")

    db = request.app.state.db
    
    # Save upload to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        await db.restore(tmp_path)
        # Clean up temp file
        os.remove(tmp_path)
        return {"success": True, "message": "Database successfully restored. Connections refreshed."}
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(status_code=500, detail=f"Database restore failed: {e}")
