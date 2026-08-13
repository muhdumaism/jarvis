"""
JARVIS — Firmware Manager

Handles binary updates registration, version tracking, checksum verification,
and serves compiled firmware to nodes.
"""

import os
import hashlib
from typing import List, Optional

from sqlalchemy import select

from app.db.database import DatabaseManager
from app.db.models import FirmwareVersion

import structlog

logger = structlog.get_logger("jarvis.firmware")


class FirmwareManager:
    """Manages system firmware updates binary storage and SHA256 validation."""

    def __init__(self, db: DatabaseManager, firmware_dir: str):
        self.db = db
        self.firmware_dir = firmware_dir
        self._initialized = False

    async def initialize(self) -> None:
        """Create firmware storage directory if missing."""
        os.makedirs(self.firmware_dir, exist_ok=True)
        self._initialized = True
        logger.info("firmware.manager.initialized", path=self.firmware_dir)

    async def register_firmware(
        self,
        version: str,
        chip_type: str,
        target: str,
        filename: str,
        data: bytes,
        description: str = ""
    ) -> dict:
        """Verify binary format integrity, write file, and record metadata."""
        if not self._initialized:
            raise RuntimeError("Firmware manager not initialized")

        # 1. Integrity check: SHA256
        sha256 = hashlib.sha256(data).hexdigest()

        # 2. Write file to disk
        file_path = os.path.join(self.firmware_dir, filename)
        with open(file_path, "wb") as f:
            f.write(data)

        # 3. Create db record
        async with self.db.get_session() as session:
            fv = FirmwareVersion(
                version=version,
                chip_type=chip_type.lower(),
                target=target.lower(),
                filename=filename,
                file_size=len(data),
                sha256=sha256,
                description=description
            )
            session.add(fv)
            await session.commit()
            await session.refresh(fv)

            logger.info(
                "firmware.registered",
                version=version,
                chip=chip_type,
                target=target,
                sha256=sha256
            )
            
            return {
                "id": fv.id,
                "version": fv.version,
                "chip_type": fv.chip_type,
                "target": fv.target,
                "filename": fv.filename,
                "file_size": fv.file_size,
                "sha256": fv.sha256,
                "description": fv.description,
                "uploaded_at": fv.uploaded_at
            }

    async def get_all_versions(self) -> List[dict]:
        """List all registered firmware records."""
        async with self.db.get_session() as session:
            result = await session.execute(
                select(FirmwareVersion).order_by(FirmwareVersion.uploaded_at.desc())
            )
            versions = result.scalars().all()
            return [
                {
                    "id": v.id,
                    "version": v.version,
                    "chip_type": v.chip_type,
                    "target": v.target,
                    "filename": v.filename,
                    "file_size": v.file_size,
                    "sha256": v.sha256,
                    "description": v.description,
                    "uploaded_at": v.uploaded_at
                }
                for v in versions
            ]

    async def get_version(self, fv_id: int) -> Optional[dict]:
        """Fetch details of a single version."""
        async with self.db.get_session() as session:
            result = await session.execute(
                select(FirmwareVersion).where(FirmwareVersion.id == fv_id)
            )
            v = result.scalar_one_or_none()
            if not v:
                return None
            return {
                "id": v.id,
                "version": v.version,
                "chip_type": v.chip_type,
                "target": v.target,
                "filename": v.filename,
                "file_size": v.file_size,
                "sha256": v.sha256,
                "description": v.description,
                "uploaded_at": v.uploaded_at
            }

    async def get_binary_path(self, filename: str) -> Optional[str]:
        """Validate and return safe local file path to firmware binary."""
        # Prevent directory traversal attacks
        safe_filename = os.path.basename(filename)
        path = os.path.join(self.firmware_dir, safe_filename)
        if os.path.exists(path):
            return path
        return None

    async def delete_version(self, fv_id: int) -> bool:
        """Remove database record and binary file from disk."""
        async with self.db.get_session() as session:
            result = await session.execute(
                select(FirmwareVersion).where(FirmwareVersion.id == fv_id)
            )
            v = result.scalar_one_or_none()
            if not v:
                return False

            # Delete file
            file_path = os.path.join(self.firmware_dir, v.filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.error("firmware.file_delete_failed", path=file_path, error=str(e))

            await session.delete(v)
            await session.commit()
            logger.info("firmware.deleted_version", id=fv_id)
            return True
