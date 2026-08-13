"""
JARVIS — Firmware API Router
"""

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form, status
from fastapi.responses import FileResponse

from app.core.security import get_current_user, require_admin
from app.firmware.schemas import FirmwareUploadResponse, FirmwareVersionResponse

router = APIRouter(prefix="/firmware", tags=["firmware"])


def _get_firmware_manager(request: Request):
    return request.app.state.firmware_manager


@router.get("", response_model=list[FirmwareVersionResponse])
async def list_versions(
    manager=Depends(_get_firmware_manager),
    _user=Depends(get_current_user)
):
    """List all registered firmware records."""
    return await manager.get_all_versions()


@router.post("/upload", response_model=FirmwareUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_firmware(
    version: str = Form(...),
    chip_type: str = Form(...),  # esp32, esp32s3
    target: str = Form(...),  # main, node
    description: str = Form(""),
    file: UploadFile = File(...),
    manager=Depends(_get_firmware_manager),
    _admin=Depends(require_admin)
):
    """Upload and register a compiled firmware binary (.bin)."""
    # Verify file extension
    if not file.filename.endswith(".bin"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only .bin files are accepted."
        )

    # Read binary content
    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty firmware binary file")

    try:
        # Register and write to disk
        meta = await manager.register_firmware(
            version=version,
            chip_type=chip_type,
            target=target,
            filename=file.filename,
            data=contents,
            description=description
        )
        return meta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register firmware: {e}")


@router.get("/{id}/download")
async def download_firmware(
    id: int,
    manager=Depends(_get_firmware_manager)
):
    """Download a compiled firmware binary by database record ID."""
    meta = await manager.get_version(id)
    if not meta:
        raise HTTPException(status_code=404, detail="Firmware version record not found")

    path = await manager.get_binary_path(meta["filename"])
    if not path:
        raise HTTPException(status_code=404, detail="Binary file missing from storage directory")

    return FileResponse(
        path,
        media_type="application/octet-stream",
        filename=meta["filename"]
    )


@router.delete("/{id}")
async def delete_version(
    id: int,
    manager=Depends(_get_firmware_manager),
    _admin=Depends(require_admin)
):
    """Remove firmware version registration and delete binary from disk."""
    if not await manager.delete_version(id):
        raise HTTPException(status_code=404, detail="Firmware version record not found")
    return {"success": True}
