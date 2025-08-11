"""
Secure storage service for encrypted file storage and access controls.
Implements enterprise-grade security for sensitive document storage.
"""

import os
import hashlib
import hmac
import json
import tempfile
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, BinaryIO, List
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from app.core.config import settings
from app.core.logging import get_logger
from app.core.audit import log_system_action
from app.core.redaction import redact_for_audit, RedactionLevel

logger = get_logger(__name__)


class SecureStorageService:
    """Enterprise-grade secure storage service for sensitive documents."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.storage_path = Path(settings.STORAGE_PATH)
        self.encryption_key = self._get_or_generate_key()
        self.fernet = Fernet(self.encryption_key)
        
        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different content types
        self.contracts_path = self.storage_path / "contracts"
        self.suppliers_path = self.storage_path / "suppliers"
        self.audit_path = self.storage_path / "audit"
        self.temp_path = self.storage_path / "temp"
        
        for path in [self.contracts_path, self.suppliers_path, self.audit_path, self.temp_path]:
            path.mkdir(exist_ok=True)
    
    def _get_or_generate_key(self) -> bytes:
        """Get encryption key from environment or generate a new one."""
        key_env = os.getenv("SUPPLERO_ENCRYPTION_KEY")
        
        if key_env:
            try:
                # Decode base64 key from environment
                return base64.urlsafe_b64decode(key_env)
            except Exception as e:
                self.logger.warning(
                    "Invalid encryption key in environment, generating new one",
                    error=str(e)
                )
        
        # Generate new key
        key = Fernet.generate_key()
        
        # Log the key generation (in production, this should be stored securely)
        self.logger.warning(
            "Generated new encryption key. Store this securely in SUPPLERO_ENCRYPTION_KEY environment variable",
            key_base64=base64.urlsafe_b64encode(key).decode()
        )
        
        return key
    
    def _generate_file_hash(self, content: bytes) -> str:
        """Generate SHA-256 hash of file content."""
        return hashlib.sha256(content).hexdigest()
    
    def _generate_hmac(self, content: bytes, salt: str) -> str:
        """Generate HMAC for content integrity verification."""
        key = self.encryption_key + salt.encode()
        return hmac.new(key, content, hashlib.sha256).hexdigest()
    
    def _get_storage_path(self, content_type: str, organization_id: str) -> Path:
        """Get appropriate storage path based on content type and organization."""
        if content_type == "contract":
            base_path = self.contracts_path
        elif content_type == "supplier":
            base_path = self.suppliers_path
        elif content_type == "audit":
            base_path = self.audit_path
        else:
            base_path = self.storage_path
        
        # Create organization-specific subdirectory
        org_path = base_path / organization_id
        org_path.mkdir(exist_ok=True)
        
        return org_path
    
    def store_file(
        self,
        content: bytes,
        filename: str,
        content_type: str,
        organization_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        encryption_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        Store a file securely with encryption and access controls.
        
        Args:
            content: File content as bytes
            filename: Original filename
            content_type: Type of content (contract, supplier, audit, etc.)
            organization_id: Organization ID for access control
            metadata: Additional metadata to store
            encryption_level: Encryption level (standard, high, critical)
            
        Returns:
            Storage metadata including file ID and access information
        """
        try:
            # Generate unique file ID
            file_id = hashlib.sha256(
                f"{organization_id}:{filename}:{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()[:16]
            
            # Get storage path
            storage_path = self._get_storage_path(content_type, organization_id)
            file_path = storage_path / f"{file_id}.enc"
            
            # Generate content hash for integrity
            content_hash = self._generate_file_hash(content)
            
            # Generate HMAC for tamper detection
            salt = os.urandom(16).hex()
            hmac_value = self._generate_hmac(content, salt)
            
            # Encrypt content
            encrypted_content = self.fernet.encrypt(content)
            
            # Prepare metadata
            file_metadata = {
                "file_id": file_id,
                "original_filename": filename,
                "content_type": content_type,
                "organization_id": organization_id,
                "content_hash": content_hash,
                "hmac": hmac_value,
                "salt": salt,
                "encryption_level": encryption_level,
                "file_size": len(content),
                "encrypted_size": len(encrypted_content),
                "created_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            # Store encrypted file
            with open(file_path, 'wb') as f:
                f.write(encrypted_content)
            
            # Store metadata separately (encrypted)
            metadata_path = storage_path / f"{file_id}.meta.enc"
            metadata_json = json.dumps(file_metadata, default=str)
            encrypted_metadata = self.fernet.encrypt(metadata_json.encode())
            
            with open(metadata_path, 'wb') as f:
                f.write(encrypted_metadata)
            
            # Log the storage action
            log_system_action(
                action="file_stored_securely",
                organization_id=organization_id,
                resource_type="secure_storage",
                resource_id=file_id,
                details={
                    "filename": filename,
                    "content_type": content_type,
                    "encryption_level": encryption_level,
                    "file_size": len(content),
                    "storage_path": str(file_path)
                }
            )
            
            self.logger.info(
                "File stored securely",
                file_id=file_id,
                filename=filename,
                content_type=content_type,
                organization_id=organization_id,
                encryption_level=encryption_level
            )
            
            return {
                "file_id": file_id,
                "storage_path": str(file_path),
                "metadata_path": str(metadata_path),
                "encryption_level": encryption_level,
                "created_at": file_metadata["created_at"]
            }
            
        except Exception as e:
            self.logger.error(
                "Failed to store file securely",
                filename=filename,
                content_type=content_type,
                organization_id=organization_id,
                error=str(e),
                exc_info=True
            )
            raise
    
    def retrieve_file(
        self,
        file_id: str,
        organization_id: str,
        content_type: str,
        verify_integrity: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieve a file securely with integrity verification.
        
        Args:
            file_id: Unique file identifier
            organization_id: Organization ID for access control
            content_type: Expected content type
            verify_integrity: Whether to verify file integrity
            
        Returns:
            File content and metadata
        """
        try:
            # Get storage path
            storage_path = self._get_storage_path(content_type, organization_id)
            file_path = storage_path / f"{file_id}.enc"
            metadata_path = storage_path / f"{file_id}.meta.enc"
            
            # Check if files exist
            if not file_path.exists() or not metadata_path.exists():
                raise FileNotFoundError(f"File {file_id} not found")
            
            # Read and decrypt metadata
            with open(metadata_path, 'rb') as f:
                encrypted_metadata = f.read()
            
            metadata_json = self.fernet.decrypt(encrypted_metadata).decode()
            metadata = json.loads(metadata_json)
            
            # Verify organization access
            if metadata["organization_id"] != organization_id:
                raise PermissionError("Access denied to this file")
            
            # Read and decrypt file content
            with open(file_path, 'rb') as f:
                encrypted_content = f.read()
            
            content = self.fernet.decrypt(encrypted_content)
            
            # Verify integrity if requested
            if verify_integrity:
                # Verify content hash
                content_hash = self._generate_file_hash(content)
                if content_hash != metadata["content_hash"]:
                    raise ValueError("File content hash mismatch - file may be corrupted")
                
                # Verify HMAC
                expected_hmac = self._generate_hmac(content, metadata["salt"])
                if not hmac.compare_digest(expected_hmac, metadata["hmac"]):
                    raise ValueError("HMAC verification failed - file may have been tampered with")
            
            # Log the retrieval action
            log_system_action(
                action="file_retrieved_securely",
                organization_id=organization_id,
                resource_type="secure_storage",
                resource_id=file_id,
                details={
                    "filename": metadata["original_filename"],
                    "content_type": content_type,
                    "integrity_verified": verify_integrity
                }
            )
            
            self.logger.info(
                "File retrieved securely",
                file_id=file_id,
                filename=metadata["original_filename"],
                content_type=content_type,
                organization_id=organization_id
            )
            
            return {
                "content": content,
                "metadata": metadata,
                "retrieved_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(
                "Failed to retrieve file securely",
                file_id=file_id,
                organization_id=organization_id,
                content_type=content_type,
                error=str(e),
                exc_info=True
            )
            raise
    
    def delete_file(
        self,
        file_id: str,
        organization_id: str,
        content_type: str
    ) -> bool:
        """
        Securely delete a file and its metadata.
        
        Args:
            file_id: Unique file identifier
            organization_id: Organization ID for access control
            content_type: Content type for path resolution
            
        Returns:
            True if deletion was successful
        """
        try:
            # Get storage path
            storage_path = self._get_storage_path(content_type, organization_id)
            file_path = storage_path / f"{file_id}.enc"
            metadata_path = storage_path / f"{file_id}.meta.enc"
            
            # Check if files exist
            if not file_path.exists() or not metadata_path.exists():
                return False
            
            # Read metadata for logging (before deletion)
            try:
                with open(metadata_path, 'rb') as f:
                    encrypted_metadata = f.read()
                metadata_json = self.fernet.decrypt(encrypted_metadata).decode()
                metadata = json.loads(metadata_json)
                filename = metadata.get("original_filename", "unknown")
            except:
                filename = "unknown"
            
            # Securely delete files
            # Overwrite with random data before deletion for secure deletion
            secure_delete_paths = [file_path, metadata_path]
            
            for path in secure_delete_paths:
                if path.exists():
                    # Overwrite with random data
                    file_size = path.stat().st_size
                    with open(path, 'wb') as f:
                        f.write(os.urandom(file_size))
                    # Delete file
                    path.unlink()
            
            # Log the deletion action
            log_system_action(
                action="file_deleted_securely",
                organization_id=organization_id,
                resource_type="secure_storage",
                resource_id=file_id,
                details={
                    "filename": filename,
                    "content_type": content_type,
                    "secure_deletion": True
                }
            )
            
            self.logger.info(
                "File deleted securely",
                file_id=file_id,
                filename=filename,
                content_type=content_type,
                organization_id=organization_id
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to delete file securely",
                file_id=file_id,
                organization_id=organization_id,
                content_type=content_type,
                error=str(e),
                exc_info=True
            )
            return False
    
    def list_files(
        self,
        organization_id: str,
        content_type: str,
        include_metadata: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List files for an organization with optional metadata.
        
        Args:
            organization_id: Organization ID
            content_type: Content type to list
            include_metadata: Whether to include decrypted metadata
            
        Returns:
            List of file information
        """
        try:
            # Get storage path
            storage_path = self._get_storage_path(content_type, organization_id)
            
            if not storage_path.exists():
                return []
            
            files = []
            
            # Find all metadata files
            for metadata_file in storage_path.glob("*.meta.enc"):
                try:
                    file_id = metadata_file.stem.replace(".meta", "")
                    
                    # Read and decrypt metadata
                    with open(metadata_file, 'rb') as f:
                        encrypted_metadata = f.read()
                    
                    metadata_json = self.fernet.decrypt(encrypted_metadata).decode()
                    metadata = json.loads(metadata_json)
                    
                    # Verify organization access
                    if metadata["organization_id"] != organization_id:
                        continue
                    
                    # Check if encrypted file exists
                    file_path = storage_path / f"{file_id}.enc"
                    if not file_path.exists():
                        continue
                    
                    file_info = {
                        "file_id": file_id,
                        "filename": metadata["original_filename"],
                        "content_type": metadata["content_type"],
                        "file_size": metadata["file_size"],
                        "encryption_level": metadata["encryption_level"],
                        "created_at": metadata["created_at"],
                        "exists": True
                    }
                    
                    if include_metadata:
                        # Redact sensitive metadata for listing
                        redacted_metadata = redact_for_audit(
                            metadata, 
                            RedactionLevel.MEDIUM
                        )
                        file_info["metadata"] = redacted_metadata
                    
                    files.append(file_info)
                    
                except Exception as e:
                    self.logger.warning(
                        "Failed to read metadata for file",
                        metadata_file=str(metadata_file),
                        error=str(e)
                    )
                    continue
            
            # Sort by creation date (newest first)
            files.sort(key=lambda x: x["created_at"], reverse=True)
            
            return files
            
        except Exception as e:
            self.logger.error(
                "Failed to list files",
                organization_id=organization_id,
                content_type=content_type,
                error=str(e),
                exc_info=True
            )
            return []
    
    def get_storage_stats(
        self,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Get storage statistics for an organization.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            Storage statistics
        """
        try:
            stats = {
                "organization_id": organization_id,
                "total_files": 0,
                "total_size_bytes": 0,
                "files_by_type": {},
                "encryption_levels": {},
                "storage_paths": {}
            }
            
            # Check all content types
            content_types = ["contract", "supplier", "audit"]
            
            for content_type in content_types:
                storage_path = self._get_storage_path(content_type, organization_id)
                
                if not storage_path.exists():
                    continue
                
                type_stats = {
                    "file_count": 0,
                    "total_size": 0,
                    "encryption_levels": {}
                }
                
                # Count files and sizes
                for file_path in storage_path.glob("*.enc"):
                    if file_path.name.endswith(".meta.enc"):
                        continue
                    
                    try:
                        file_size = file_path.stat().st_size
                        type_stats["file_count"] += 1
                        type_stats["total_size"] += file_size
                        
                        # Get encryption level from metadata
                        metadata_file = storage_path / f"{file_path.stem}.meta.enc"
                        if metadata_file.exists():
                            with open(metadata_file, 'rb') as f:
                                encrypted_metadata = f.read()
                            metadata_json = self.fernet.decrypt(encrypted_metadata).decode()
                            metadata = json.loads(metadata_json)
                            
                            encryption_level = metadata.get("encryption_level", "unknown")
                            type_stats["encryption_levels"][encryption_level] = \
                                type_stats["encryption_levels"].get(encryption_level, 0) + 1
                        
                    except Exception as e:
                        self.logger.warning(
                            "Failed to get file stats",
                            file_path=str(file_path),
                            error=str(e)
                        )
                
                stats["files_by_type"][content_type] = type_stats
                stats["total_files"] += type_stats["file_count"]
                stats["total_size_bytes"] += type_stats["total_size"]
                
                # Aggregate encryption levels
                for level, count in type_stats["encryption_levels"].items():
                    stats["encryption_levels"][level] = \
                        stats["encryption_levels"].get(level, 0) + count
                
                stats["storage_paths"][content_type] = str(storage_path)
            
            return stats
            
        except Exception as e:
            self.logger.error(
                "Failed to get storage stats",
                organization_id=organization_id,
                error=str(e),
                exc_info=True
            )
            return {
                "organization_id": organization_id,
                "error": str(e)
            }


# Global secure storage service instance
secure_storage = SecureStorageService()


def get_secure_storage() -> SecureStorageService:
    """Get the global secure storage service instance."""
    return secure_storage 