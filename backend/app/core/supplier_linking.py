"""
Supplier Linking Service

This service automatically extracts supplier names from contract documents and links them
to database suppliers using intelligent fuzzy matching. It integrates with the document
processing pipeline to ensure all new contracts are automatically linked.
"""

import re
from typing import Optional, Dict, Any, List
from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models.supplier import Supplier
from app.core.logging import get_logger

logger = get_logger(__name__)


class SupplierLinkingService:
    """Service for automatically linking contract documents to suppliers"""
    
    def __init__(self):
        self.legal_suffixes = [
            'Co.', 'Corp.', 'Corporation', 'Inc.', 'LLC', 'Ltd.', 'Limited', 
            'Company', 'Co', 'Corp', 'Inc', 'LLC', 'Ltd', 'Limited'
        ]
    
    def extract_supplier_name_from_contract(self, text_content: str, metadata: Dict[str, Any]) -> Optional[str]:
        """
        Extract supplier name from contract text content and metadata.
        
        Args:
            text_content: The extracted text from the contract
            metadata: The extracted metadata (dates, amounts, parties, etc.)
            
        Returns:
            Extracted supplier name or None if not found
        """
        if not text_content:
            return None
        
        # Method 1: Look for supplier name in parties metadata
        supplier_name = self._extract_from_parties_metadata(metadata)
        if supplier_name:
            return supplier_name
        
        # Method 2: Look for supplier patterns in the full text
        supplier_name = self._extract_from_full_text(text_content)
        if supplier_name:
            return supplier_name
        
        # Method 3: Look for common contract patterns
        supplier_name = self._extract_from_contract_patterns(text_content)
        if supplier_name:
            return supplier_name
        
        return None
    
    def _extract_from_parties_metadata(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Extract supplier name from parties metadata."""
        if not metadata or 'parties' not in metadata:
            return None
        
        parties = metadata.get('parties', [])
        for party in parties:
            if party.get('value') == 'Supplier' and party.get('context'):
                context = party.get('context', '')
                supplier_name = self._extract_supplier_from_context(context)
                if supplier_name:
                    return supplier_name
        
        return None
    
    def _extract_from_full_text(self, text_content: str) -> Optional[str]:
        """Extract supplier name from full contract text."""
        # Look for supplier name patterns in the text
        supplier_patterns = [
            r'SUPPLIER:\s*([^\n\r]+)',
            r'VENDOR:\s*([^\n\r]+)',
            r'CONTRACTOR:\s*([^\n\r]+)',
            r'PROVIDER:\s*([^\n\r]+)',
            r'SELLER:\s*([^\n\r]+)',
            r'PARTY B:\s*([^\n\r]+)',
        ]
        
        for pattern in supplier_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                supplier_name = match.group(1).strip()
                # Clean up the supplier name
                supplier_name = self._clean_supplier_name(supplier_name)
                if supplier_name:
                    return supplier_name
        
        return None
    
    def _extract_from_contract_patterns(self, text_content: str) -> Optional[str]:
        """Extract supplier name using contract-specific patterns."""
        # Look for company patterns in contract text
        company_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Technologies?|Corp|Inc|Ltd|LLC|Company|Co))',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Manufacturing|Solutions|Systems|Services))',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:International|Global|Worldwide))',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Group|Partners|Associates))'
        ]
        
        # Look for these patterns but exclude common buyer names
        excluded_terms = ['techcorp', 'buyer', 'client', 'customer', 'our company', 'we', 'us']
        
        for pattern in company_patterns:
            matches = re.findall(pattern, text_content)
            for match in matches:
                match_lower = match.lower()
                # Check if this match contains excluded terms
                if not any(excluded in match_lower for excluded in excluded_terms):
                    supplier_name = self._clean_supplier_name(match)
                    if supplier_name:
                        return supplier_name
        
        return None
    
    def _extract_supplier_from_context(self, context: str) -> Optional[str]:
        """Extract supplier name from context text."""
        # Look for supplier name after "SUPPLIER:" or similar indicators
        supplier_patterns = [
            r'SUPPLIER:\s*([^\n\r]+)',
            r'VENDOR:\s*([^\n\r]+)',
            r'CONTRACTOR:\s*([^\n\r]+)',
        ]
        
        for pattern in supplier_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                supplier_name = match.group(1).strip()
                supplier_name = self._clean_supplier_name(supplier_name)
                if supplier_name:
                    return supplier_name
        
        return None
    
    def _clean_supplier_name(self, supplier_name: str) -> Optional[str]:
        """Clean and normalize supplier name."""
        if not supplier_name or len(supplier_name.strip()) < 3:
            return None
        
        # Remove common legal suffixes more carefully
        cleaned_name = supplier_name
        for suffix in self.legal_suffixes:
            # Use word boundaries to avoid partial matches
            suffix_pattern = r'\b' + re.escape(suffix) + r'\b'
            cleaned_name = re.sub(suffix_pattern, '', cleaned_name, flags=re.IGNORECASE)
        
        # Remove extra whitespace and punctuation
        cleaned_name = re.sub(r'\s+', ' ', cleaned_name.strip())
        cleaned_name = re.sub(r'[^\w\s\-\.&]', '', cleaned_name)
        
        # Clean up any remaining artifacts from suffix removal
        cleaned_name = re.sub(r'\s+\.\s*\.\s*', ' ', cleaned_name)  # Remove double dots
        cleaned_name = re.sub(r'^\s*\.\s*', '', cleaned_name)  # Remove leading dots
        cleaned_name = re.sub(r'\s*\.\s*$', '', cleaned_name)  # Remove trailing dots
        
        # Ensure we have a meaningful name
        if len(cleaned_name.strip()) < 3:
            return None
        
        return cleaned_name.strip()
    
    def find_best_supplier_match(self, contract_supplier_name: str, database_suppliers: List[Supplier]) -> Optional[Supplier]:
        """
        Find the best matching supplier using fuzzy matching.
        
        Args:
            contract_supplier_name: Supplier name extracted from contract
            database_suppliers: List of suppliers from database
            
        Returns:
            Best matching supplier or None if no good match found
        """
        if not contract_supplier_name or not database_suppliers:
            return None
        
        # Clean and normalize the contract supplier name
        cleaned_contract_name = self._normalize_supplier_name(contract_supplier_name)
        
        best_match = None
        best_score = 0
        
        for supplier in database_suppliers:
            cleaned_db_name = self._normalize_supplier_name(supplier.name)
            
            # Calculate similarity score using different methods
            # Method 1: Sequence matcher (good for general similarity)
            sequence_score = SequenceMatcher(None, cleaned_contract_name, cleaned_db_name).ratio()
            
            # Method 2: Check if one contains the other (good for abbreviations)
            contains_score = 0
            if cleaned_contract_name in cleaned_db_name or cleaned_db_name in cleaned_contract_name:
                contains_score = 0.8
            
            # Method 3: Check for key words (good for company name variations)
            contract_words = set(cleaned_contract_name.split())
            db_words = set(cleaned_db_name.split())
            common_words = contract_words.intersection(db_words)
            word_score = len(common_words) / max(len(contract_words), len(db_words)) if contract_words and db_words else 0
            
            # Combine scores
            total_score = max(sequence_score, contains_score, word_score)
            
            if total_score > best_score and total_score > 0.6:  # 60% threshold
                best_score = total_score
                best_match = supplier
        
        return best_match
    
    def _normalize_supplier_name(self, name: str) -> str:
        """Normalize supplier name for comparison."""
        if not name:
            return ""
        
        # Remove common legal suffixes
        normalized_name = name
        for suffix in self.legal_suffixes:
            normalized_name = normalized_name.replace(suffix, '').replace(suffix.replace('.', ''), '')
        
        # Remove extra whitespace and punctuation
        normalized_name = re.sub(r'\s+', ' ', normalized_name.strip())
        normalized_name = re.sub(r'[^\w\s\-\.&]', '', normalized_name)
        
        return normalized_name.lower()
    
    def extract_contract_value(self, metadata: Dict[str, Any]) -> Optional[float]:
        """
        Extract contract value from metadata.
        
        Args:
            metadata: The extracted metadata from the document
            
        Returns:
            Contract value as float or None if not found
        """
        if not metadata:
            return None
        
        amounts = metadata.get('amounts', [])
        for amount in amounts:
            value = amount.get('value', '')
            if '$' in value and ',' in value:
                try:
                    # Clean up the value string
                    clean_value = value.replace('$', '').replace(',', '').replace(' USD', '').replace('USD', '')
                    clean_value = re.sub(r'[^\d.]', '', clean_value)  # Keep only digits and decimal point
                    if clean_value:
                        contract_value = float(clean_value)
                        # Look for the main contract value (usually the largest amount)
                        if contract_value > 100000:  # Filter out small amounts
                            return contract_value
                except (ValueError, TypeError):
                    continue
        
        return None
    
    async def link_contract_to_supplier(
        self, 
        document_id: int, 
        db: Session, 
        organization_id: int
    ) -> bool:
        """
        Automatically link a contract document to a supplier.
        
        Args:
            document_id: ID of the document to link
            db: Database session
            organization_id: Organization ID for filtering suppliers
            
        Returns:
            True if linking was successful, False otherwise
        """
        try:
            # Get the document
            from app.models.document import Document
            document = db.query(Document).filter(Document.id == document_id).first()
            
            if not document:
                logger.error(f"Document {document_id} not found for supplier linking")
                return False
            
            # Check if document already has supplier linking
            if document.extracted_metadata and document.extracted_metadata.get('supplier_name'):
                logger.info(f"Document {document_id} already has supplier linking: {document.extracted_metadata.get('supplier_name')}")
                return True
            
            # Get all suppliers for this organization
            suppliers = db.query(Supplier).filter(
                Supplier.organization_id == organization_id
            ).all()
            
            if not suppliers:
                logger.warning(f"No suppliers found for organization {organization_id}")
                return False
            
            # Extract supplier name from contract
            if not document.extracted_text:
                logger.warning(f"Document {document_id} has no extracted text for supplier linking")
                return False
            
            supplier_name = self.extract_supplier_name_from_contract(
                document.extracted_text, 
                document.extracted_metadata or {}
            )
            
            if not supplier_name:
                logger.info(f"No supplier name extracted from document {document_id}")
                return False
            
            # Find best matching supplier
            best_match_supplier = self.find_best_supplier_match(supplier_name, suppliers)
            
            if best_match_supplier:
                logger.info(f"Linking document {document_id} to supplier: {best_match_supplier.name}")
                
                # Update the metadata to include supplier linking
                if not document.extracted_metadata:
                    document.extracted_metadata = {}
                
                document.extracted_metadata['supplier_name'] = best_match_supplier.name
                document.extracted_metadata['supplier_id'] = best_match_supplier.id
                
                # Extract and add contract value if available
                contract_value = self.extract_contract_value(document.extracted_metadata)
                if contract_value:
                    document.extracted_metadata['contract_amount'] = contract_value
                
                # Mark the field as modified so SQLAlchemy detects the change
                flag_modified(document, "extracted_metadata")
                
                # Commit changes
                db.commit()
                
                logger.info(f"Successfully linked document {document_id} to supplier {best_match_supplier.name}")
                return True
            else:
                logger.info(f"No matching supplier found for '{supplier_name}' in document {document_id}")
                # Still add the extracted name for reference
                if not document.extracted_metadata:
                    document.extracted_metadata = {}
                
                document.extracted_metadata['supplier_name'] = supplier_name
                flag_modified(document, "extracted_metadata")
                db.commit()
                
                return False
                
        except Exception as e:
            logger.error(f"Error linking contract to supplier for document {document_id}: {str(e)}")
            return False


# Global instance
supplier_linking_service = SupplierLinkingService()
