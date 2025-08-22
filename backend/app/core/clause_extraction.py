"""
Clause Extraction Service

This service extracts and analyzes contract clauses using AI-powered analysis.
It supports the enhanced contract discovery system with clause-based queries.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class ClauseExtractionService:
    """Service for extracting contract clauses using pure OpenAI AI analysis"""
    
    def __init__(self):
        # Remove regex patterns - we'll use pure AI
        self.clause_types = [
            "payment_terms", "delivery_schedule", "penalty", "termination", 
            "liability", "force_majeure", "confidentiality", "intellectual_property",
            "governing_law", "dispute_resolution", "scope_of_work", "quality_standards",
            "warranty", "indemnification", "insurance", "compliance", "audit_rights",
            "change_management", "performance_metrics", "environmental_compliance"
        ]
    
    async def extract_clauses(self, document_text: str, document_id: str) -> List[Dict[str, Any]]:
        """Extract clauses using pure OpenAI AI analysis"""
        try:
            logger.info(
                f"Starting pure AI clause extraction for document {document_id}, text length: {len(document_text)}"
            )
            
            # Phase 1: Pure AI clause detection
            ai_detected_clauses = await self._detect_clauses_with_ai(document_text, document_id)
            
            # Phase 2: Risk assessment and metadata enrichment
            enriched_clauses = self._enrich_clause_metadata(ai_detected_clauses)
            
            logger.info(
                f"AI clause extraction completed for document {document_id}: {len(enriched_clauses)} clauses found"
            )
            
            return enriched_clauses
            
        except Exception as e:
            logger.error(
                f"AI clause extraction failed for document {document_id}: {str(e)}"
            )
            return []
    
    async def extract_clauses_from_document(
        self,
        document_text: str,
        document_id: str,
        organization_id: str
    ) -> List[Dict[str, Any]]:
        """
        Extract clauses from a document using pure OpenAI AI analysis
        (Maintains compatibility with existing code)
        
        Args:
            document_text: The text content of the document
            document_id: Unique identifier for the document
            organization_id: Organization ID for the document (not used in pure AI approach)
            
        Returns:
            List of extracted clauses with analysis
        """
        return await self.extract_clauses(document_text, document_id)
    
    async def _detect_clauses_with_ai(
        self, 
        document_text: str, 
        document_id: str
    ) -> List[Dict[str, Any]]:
        """Detect ALL clauses using OpenAI AI analysis"""
        try:
            # Check if OpenAI API key is available
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                logger.error("OpenAI API key not found - AI clause extraction cannot proceed")
                return []
            
            # Import OpenAI client
            try:
                from openai import OpenAI
                client = OpenAI(api_key=openai_api_key)
            except ImportError:
                logger.error("OpenAI client not available - AI clause extraction cannot proceed")
                return []
            
            # Prepare comprehensive AI prompt for clause analysis
            ai_prompt = f"""
            You are a contract analysis expert. Analyze this contract document and identify ALL contract clauses present.
            
            Document Text (first 4000 characters):
            {document_text[:4000]}
            
            Available clause types to identify:
            {', '.join(self.clause_types)}
            
            For each clause you find, provide:
            1. clause_type: Choose from the available types above, or use "other" if none fit
            2. clause_text: The exact text of the clause (be precise)
            3. extracted_text: Context around the clause (100-200 characters)
            4. confidence_score: 0.0 to 1.0 (how certain you are this is a clause)
            5. risk_level: low, medium, high, or critical (assess the business risk)
            6. reasoning: Why this clause was identified and its significance
            
            IMPORTANT: 
            - Be thorough but accurate. Only identify actual contract clauses, not general text.
            - Return ONLY a valid JSON array of clauses found.
            - Do NOT include any explanatory text before or after the JSON.
            - Ensure the JSON is properly formatted and valid.
            
            Example format:
            [
              {{
                "clause_type": "payment_terms",
                "clause_text": "Payment is due within 30 days of invoice receipt",
                "extracted_text": "Payment Terms: Payment is due within 30 days of invoice receipt. Late payments will incur a 2% monthly fee...",
                "confidence_score": 0.95,
                "risk_level": "medium",
                "reasoning": "Clear payment terms with specific timeline and late payment consequences"
              }}
            ]
            
            If no clauses found, return: []
            
            Remember: Return ONLY the JSON array, nothing else.
            """
            
            # Call OpenAI with higher token limit for comprehensive analysis
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a contract analysis AI expert. Identify ALL contract clauses and return only valid JSON arrays. Be thorough and accurate."},
                    {"role": "user", "content": ai_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent, accurate results
                max_tokens=2000   # Higher token limit for comprehensive clause analysis
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content.strip()
            logger.info(f"AI clause analysis response received: {ai_response[:500]}...")
            
            # Extract JSON from response - improved parsing logic
            try:
                import re
                
                # First, try to find JSON array with more flexible regex
                # Look for content between [ and ] that might contain newlines
                json_match = re.search(r'\[[\s\S]*\]', ai_response)
                
                if json_match:
                    json_content = json_match.group()
                    logger.info(f"Found JSON content: {json_content[:300]}...")
                    
                    # Try to parse the JSON
                    ai_clauses = json.loads(json_content)
                    
                    # Convert AI results to our format
                    detected_clauses = []
                    for ai_clause in ai_clauses:
                        detected_clauses.append({
                            "clause_type": ai_clause.get("clause_type", "other"),
                            "clause_text": ai_clause.get("clause_text", ""),
                            "extracted_text": ai_clause.get("extracted_text", ""),
                            "confidence_score": ai_clause.get("confidence_score", 0.8),
                            "risk_level": ai_clause.get("risk_level", "medium"),
                            "metadata": {
                                "ai_enhanced": True,
                                "reasoning": ai_clause.get("reasoning", ""),
                                "source": "openai_analysis",
                                "extraction_method": "pure_ai"
                            }
                        })
                    
                    logger.info(f"AI detected {len(detected_clauses)} clauses")
                    return detected_clauses
                else:
                    # If no JSON array found, try to find any JSON-like content
                    logger.warning("No JSON array found, trying alternative parsing...")
                    
                    # Look for any content that might be JSON
                    if '{' in ai_response and '}' in ai_response:
                        # Try to extract content between { and }
                        json_objects = re.findall(r'\{[^{}]*\}', ai_response)
                        if json_objects:
                            logger.info(f"Found {len(json_objects)} potential JSON objects")
                            # Convert single objects to array format
                            detected_clauses = []
                            for obj_str in json_objects:
                                try:
                                    obj = json.loads(obj_str)
                                    detected_clauses.append({
                                        "clause_type": obj.get("clause_type", "other"),
                                        "clause_text": obj.get("clause_text", ""),
                                        "extracted_text": obj.get("extracted_text", ""),
                                        "confidence_score": obj.get("confidence_score", 0.8),
                                        "risk_level": obj.get("risk_level", "medium"),
                                        "metadata": {
                                            "ai_enhanced": True,
                                            "reasoning": obj.get("reasoning", ""),
                                            "source": "openai_analysis",
                                            "extraction_method": "pure_ai"
                                        }
                                    })
                                except json.JSONDecodeError:
                                    continue
                            
                            if detected_clauses:
                                logger.info(f"Successfully parsed {len(detected_clauses)} clauses from individual objects")
                                return detected_clauses
                    
                    logger.warning("No valid JSON content found in AI response")
                    logger.warning(f"Full AI response: {ai_response}")
                    return []
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                logger.error(f"JSON content that failed: {json_match.group() if json_match else 'None'}")
                return []
                
        except Exception as e:
            logger.error(f"AI clause detection failed: {str(e)}")
            return []
    
    def _assess_risk_level(self, clause_type: str) -> str:
        """Assess risk level for a clause type"""
        high_risk_clauses = [
            'liability', 'indemnification', 'penalty', 'termination'
        ]
        medium_risk_clauses = [
            'force_majeure', 'export_control', 'non_compete', 'exclusivity'
        ]
        
        if clause_type in high_risk_clauses:
            return 'high'
        elif clause_type in medium_risk_clauses:
            return 'medium'
        else:
            return 'low'
    
    def _enrich_clause_metadata(self, clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich clause metadata with additional information"""
        enriched_clauses = []
        
        for clause_data in clauses:
            # Add extraction timestamp and additional metadata
            enriched_clause = clause_data.copy()
            enriched_clause['metadata'] = clause_data.get('metadata', {}).copy()
            enriched_clause['metadata']['extracted_at'] = datetime.utcnow().isoformat()
            enriched_clause['metadata']['processing_version'] = 'pure_openai_v1'
            
            # Ensure confidence score is within valid range
            if 'confidence_score' in enriched_clause:
                enriched_clause['confidence_score'] = max(0.0, min(1.0, enriched_clause['confidence_score']))
            
            # Ensure risk level is valid
            valid_risk_levels = ['low', 'medium', 'high', 'critical']
            if enriched_clause.get('risk_level') not in valid_risk_levels:
                enriched_clause['risk_level'] = 'medium'
            
            enriched_clauses.append(enriched_clause)
        
        return enriched_clauses
    
    async def search_clauses_by_type(
        self,
        clause_type: str,
        search_text: Optional[str] = None,
        risk_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for clauses by type and criteria"""
        # This would typically query a database of extracted clauses
        # For now, return empty list as placeholder
        return []
    
    async def get_clause_statistics(
        self,
        organization_id: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get statistics about extracted clauses"""
        # This would typically aggregate data from a database
        # For now, return placeholder statistics
        return {
            "total_clauses": 0,
            "clauses_by_type": {},
            "risk_distribution": {},
            "compliance_gaps": 0
        }
