"""
Simple document storage service for the document ingestion pipeline.
This is a simplified version that provides the basic functionality needed.
"""

import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

from app.core.logging import get_logger

logger = get_logger(__name__)


class DocumentStorage:
    """Simple document storage service for document ingestion"""
    
    def __init__(self, base_path: str = "uploads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info("Document storage initialized", base_path=str(self.base_path))
    
    async def store_file(self, file_path: str, file_content: bytes) -> str:
        """Store a file and return the actual file path"""
        try:
            # Ensure the directory exists
            full_path = self.base_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the file
            with open(full_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(
                "File stored successfully",
                file_path=str(full_path),
                file_size=len(file_content)
            )
            
            return str(full_path)
            
        except Exception as e:
            logger.error(
                "Failed to store file",
                file_path=file_path,
                error=str(e)
            )
            raise
    
    async def get_file(self, file_path: str) -> bytes:
        """Retrieve a file's content"""
        try:
            full_path = self.base_path / file_path
            
            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            with open(full_path, 'rb') as f:
                content = f.read()
            
            logger.debug(
                "File retrieved successfully",
                file_path=str(full_path),
                file_size=len(content)
            )
            
            return content
            
        except Exception as e:
            logger.error(
                "Failed to retrieve file",
                file_path=file_path,
                error=str(e)
            )
            raise
    
    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists"""
        full_path = self.base_path / file_path
        return full_path.exists()
    
    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        full_path = self.base_path / file_path
        if full_path.exists():
            return full_path.stat().st_size
        return 0
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file"""
        try:
            full_path = self.base_path / file_path
            
            if full_path.exists():
                full_path.unlink()
                logger.info("File deleted", file_path=str(full_path))
                return True
            else:
                logger.warning("File not found for deletion", file_path=str(full_path))
                return False
                
        except Exception as e:
            logger.error(
                "Failed to delete file",
                file_path=file_path,
                error=str(e)
            )
            return False
    
    def list_files(self, directory: str = "") -> list:
        """List files in a directory"""
        try:
            dir_path = self.base_path / directory
            if not dir_path.exists():
                return []
            
            files = []
            for item in dir_path.iterdir():
                if item.is_file():
                    files.append({
                        "name": item.name,
                        "path": str(item.relative_to(self.base_path)),
                        "size": item.stat().st_size,
                        "modified": datetime.fromtimestamp(item.stat().st_mtime)
                    })
            
            return files
            
        except Exception as e:
            logger.error(
                "Failed to list files",
                directory=directory,
                error=str(e)
            )
            return []
    
    def get_storage_stats(self) -> dict:
        """Get storage statistics"""
        try:
            total_files = 0
            total_size = 0
            
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.is_file():
                        total_files += 1
                        total_size += file_path.stat().st_size
            
            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "base_path": str(self.base_path)
            }
            
        except Exception as e:
            logger.error("Failed to get storage stats", error=str(e))
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "base_path": str(self.base_path),
                "error": str(e)
            }
