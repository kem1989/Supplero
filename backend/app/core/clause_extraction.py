"""
Clause Extraction Service

This service extracts and analyzes contract clauses using AI-powered analysis.
It supports the enhanced contract discovery system with clause-based queries.
"""

import json
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import structlog

from app.core.config import settings
from app.core.logging import get_logger
from app.core.ai_assistant import AIAssistantService

logger = get_logger(__name__)


class ClauseType(str, Enum):
    """Types of contract clauses that can be extracted"""
    FORCE_MAJEURE = "force_majeure"
    EXPORT_CONTROL = "export_control"
    PENALTY = "penalty"
    TERMINATION = "termination"
    PAYMENT_TERMS = "payment_terms"
    NON_COMPETE = "non_compete"
    EXCLUSIVITY = "exclusivity"
    LIABILITY = "liability"
    INDEMNIFICATION = "indemnification"
    CONFIDENTIALITY = "confidentiality"
    GOVERNING_LAW = "governing_law"
    DISPUTE_RESOLUTION = "dispute_resolution"
    PERFORMANCE_METRICS = "performance_metrics"
    LIQUIDATED_DAMAGES = "liquidated_damages"
    OTHER = "other"


class ClauseExtractionResult:
    """Result of clause extraction from a document"""
    
    def __init__(
        self,
        clause_type: ClauseType,
        clause_text: str,
        extracted_text: str,
        confidence_score: float,
        risk_level: str,
        metadata: Dict[str, Any]
    ):
        self.clause_type = clause_type
        self.clause_text = clause_text
        self.extracted_text = extracted_text
        self.confidence_score = confidence_score
        self.risk_level = risk_level
        self.metadata = metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "clause_type": self.clause_type.value,
            "clause_text": self.clause_text,
            "extracted_text": self.extracted_text,
            "confidence_score": self.confidence_score,
            "risk_level": self.risk_level,
            "metadata": self.metadata,
            "extracted_at": datetime.utcnow().isoformat()
        }


class ClauseExtractionService:
    """Service for extracting and analyzing contract clauses"""
    
    def __init__(self):
        self.ai_service = AIAssistantService()
        self.clause_patterns = self._initialize_clause_patterns()
    
    def _initialize_clause_patterns(self) -> Dict[str, List[str]]:
        """Initialize regex patterns for different clause types"""
        return {
            ClauseType.FORCE_MAJEURE.value: [
                r'\bforce\s+majeure\b',
                r'\bact\s+of\s+god\b',
                r'\bunforeseen\s+circumstances\b',
                r'\bimpossible\s+to\s+perform\b'
            ],
            ClauseType.EXPORT_CONTROL.value: [
                r'\bexport\s+control\b',
                r'\bexport\s+regulations\b',
                r'\bexport\s+compliance\b',
                r'\bexport\s+licenses\b'
            ],
            ClauseType.PENALTY.value: [
                r'\bpenalty\b',
                r'\blate\s+fees\b',
                r'\bdefault\s+charges\b',
                r'\bbreach\s+penalties\b'
            ],
            ClauseType.TERMINATION.value: [
                r'\btermination\b',
                r'\bearly\s+termination\b',
                r'\bterminate\s+agreement\b',
                r'\bcancel\s+contract\b'
            ],
            ClauseType.PAYMENT_TERMS.value: [
                r'\bpayment\s+terms\b',
                r'\bpayment\s+schedule\b',
                r'\bnet\s+\d+\b',
                r'\bpayment\s+due\b'
            ],
            ClauseType.NON_COMPETE.value: [
                r'\bnon.?compete\b',
                r'\bnon.?competition\b',
                r'\bcompete\s+with\b',
                r'\bcompetitive\s+activities\b'
            ],
            ClauseType.EXCLUSIVITY.value: [
                r'\bexclusive\b',
                r'\bexclusivity\b',
                r'\bsole\s+supplier\b',
                r'\bexclusive\s+rights\b'
            ],
            ClauseType.LIABILITY.value: [
                r'\bliability\b',
                r'\blimitation\s+of\s+liability\b',
                r'\bdamages\b',
                r'\bresponsibility\b'
            ],
            ClauseType.INDEMNIFICATION.value: [
                r'\bindemnification\b',
                r'\bindemnify\b',
                r'\bhold\s+harmless\b',
                r'\bdefend\b'
            ],
            ClauseType.CONFIDENTIALITY.value: [
                r'\bconfidentiality\b',
                r'\bconfidential\b',
                r'\bnon.?disclosure\b',
                r'\bproprietary\b'
            ],
            ClauseType.GOVERNING_LAW.value: [
                r'\bgoverning\s+law\b',
                r'\bjurisdiction\b',
                r'\bvenue\b',
                r'\bapplicable\s+law\b'
            ],
            ClauseType.DISPUTE_RESOLUTION.value: [
                r'\bdispute\s+resolution\b',
                r'\barbitration\b',
                r'\blitigation\b',
                r'\bmediation\b'
            ],
            ClauseType.PERFORMANCE_METRICS.value: [
                r'\bperformance\s+metrics\b',
                r'\bkey\s+performance\s+indicators\b',
                r'\bservice\s+levels\b',
                r'\bperformance\s+standards\b'
            ],
            ClauseType.LIQUIDATED_DAMAGES.value: [
                r'\bliquidated\s+damages\b',
                r'\bliquidated\s+damage\b',
                r'\bpre.?agreed\s+damages\b',
                r'\bstipulated\s+damages\b'
            ]
        }
    
    async def extract_clauses_from_document(
        self,
        document_text: str,
        document_id: str,
        organization_id: str
    ) -> List[ClauseExtractionResult]:
        """
        Extract clauses from a document using AI-powered analysis
        
        Args:
            document_text: The text content of the document
            document_id: Unique identifier for the document
            organization_id: Organization ID for the document
            
        Returns:
            List of extracted clauses with analysis
        """
        try:
            logger.info(
                "Extracting clauses from document",
                document_id=document_id,
                organization_id=organization_id,
                text_length=len(document_text)
            )
            
            # Phase 1: Pattern-based clause detection
            pattern_matches = self._detect_clauses_by_pattern(document_text)
            
            # Phase 2: AI-powered clause analysis and refinement
            ai_enhanced_clauses = await self._enhance_clauses_with_ai(
                document_text, pattern_matches, document_id
            )
            
            # Phase 3: Risk assessment and metadata enrichment
            enriched_clauses = self._enrich_clause_metadata(ai_enhanced_clauses)
            
            logger.info(
                "Clause extraction completed",
                document_id=document_id,
                clauses_found=len(enriched_clauses)
            )
            
            return enriched_clauses
            
        except Exception as e:
            logger.error(
                "Clause extraction failed",
                document_id=document_id,
                error=str(e)
            )
            return []
    
    def _detect_clauses_by_pattern(self, text: str) -> List[Dict[str, Any]]:
        """Detect clauses using regex patterns"""
        detected_clauses = []
        
        for clause_type, patterns in self.clause_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Extract context around the match
                    start = max(0, match.start() - 200)
                    end = min(len(text), match.end() + 200)
                    context = text[start:end]
                    
                    detected_clauses.append({
                        "clause_type": clause_type,
                        "pattern": pattern,
                        "match_text": match.group(),
                        "start_pos": match.start(),
                        "end_pos": match.end(),
                        "context": context,
                        "confidence_score": 0.7  # Base confidence for pattern matches
                    })
        
        return detected_clauses
    
    async def _enhance_clauses_with_ai(
        self,
        document_text: str,
        pattern_matches: List[Dict[str, Any]],
        document_id: str
    ) -> List[ClauseExtractionResult]:
        """Enhance clause detection using AI analysis"""
        enhanced_clauses = []
        
        for match in pattern_matches:
            try:
                # Use AI to analyze the detected clause
                ai_analysis = await self._analyze_clause_with_ai(
                    match["context"], match["clause_type"], document_text
                )
                
                if ai_analysis.get("is_valid_clause", False):
                    clause_result = ClauseExtractionResult(
                        clause_type=ClauseType(match["clause_type"]),
                        clause_text=match["match_text"],
                        extracted_text=ai_analysis.get("extracted_text", match["context"]),
                        confidence_score=ai_analysis.get("confidence_score", match["confidence_score"]),
                        risk_level=ai_analysis.get("risk_level", "medium"),
                        metadata={
                            "ai_analysis": ai_analysis,
                            "pattern_match": match,
                            "document_id": document_id
                        }
                    )
                    enhanced_clauses.append(clause_result)
                    
            except Exception as e:
                logger.warning(
                    "AI enhancement failed for clause",
                    clause_type=match["clause_type"],
                    error=str(e)
                )
                # Fall back to pattern-based result
                continue
        
        return enhanced_clauses
    
    async def _analyze_clause_with_ai(
        self,
        clause_context: str,
        clause_type: str,
        full_document: str
    ) -> Dict[str, Any]:
        """Use AI to analyze a detected clause"""
        try:
            # Build prompt for clause analysis
            prompt = self._build_clause_analysis_prompt(clause_context, clause_type)
            
            # Use OpenAI for analysis
            response = await self.ai_service._call_openai(
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Analyze this clause: {clause_context}"}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse AI response
            return self._parse_ai_clause_analysis(response)
            
        except Exception as e:
            logger.error("AI clause analysis failed", error=str(e))
            return {
                "is_valid_clause": True,
                "confidence_score": 0.7,
                "risk_level": "medium",
                "extracted_text": clause_context
            }
    
    def _build_clause_analysis_prompt(self, clause_context: str, clause_type: str) -> str:
        """Build prompt for AI clause analysis"""
        return f"""
You are a contract analysis expert. Analyze the provided clause context and determine:

1. Is this a valid {clause_type} clause?
2. What is the confidence level (0.0-1.0)?
3. What is the risk level (low/medium/high/critical)?
4. Extract the complete clause text.

Clause type: {clause_type}
Context: {clause_context}

Respond in this JSON format:
{{
    "is_valid_clause": true/false,
    "confidence_score": 0.85,
    "risk_level": "medium",
    "extracted_text": "Complete clause text here",
    "analysis": "Brief analysis of the clause"
}}

Be precise and only return valid JSON.
"""
    
    def _parse_ai_clause_analysis(self, response: str) -> Dict[str, Any]:
        """Parse AI response for clause analysis"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    "is_valid_clause": True,
                    "confidence_score": 0.7,
                    "risk_level": "medium",
                    "extracted_text": "",
                    "analysis": "Unable to parse AI response"
                }
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse AI clause analysis", response=response, error=str(e))
            return {
                "is_valid_clause": True,
                "confidence_score": 0.7,
                "risk_level": "medium",
                "extracted_text": "",
                "analysis": "JSON parsing failed"
            }
    
    def _enrich_clause_metadata(self, clauses: List[ClauseExtractionResult]) -> List[ClauseExtractionResult]:
        """Enrich clause metadata with additional analysis"""
        for clause in clauses:
            # Add risk indicators based on clause content
            risk_indicators = self._identify_risk_indicators(clause)
            clause.metadata["risk_indicators"] = risk_indicators
            
            # Add compliance flags
            compliance_flags = self._identify_compliance_flags(clause)
            clause.metadata["compliance_flags"] = compliance_flags
            
            # Add business impact assessment
            business_impact = self._assess_business_impact(clause)
            clause.metadata["business_impact"] = business_impact
        
        return clauses
    
    def _identify_risk_indicators(self, clause: ClauseExtractionResult) -> List[str]:
        """Identify specific risk indicators in a clause"""
        risk_indicators = []
        text_lower = clause.clause_text.lower()
        
        if clause.clause_type == ClauseType.FORCE_MAJEURE:
            if "pandemic" not in text_lower and "epidemic" not in text_lower:
                risk_indicators.append("Missing pandemic coverage")
            if "cyber" not in text_lower and "cybersecurity" not in text_lower:
                risk_indicators.append("Missing cyber incident coverage")
        
        elif clause.clause_type == ClauseType.PENALTY:
            # Look for percentage-based penalties
            percentage_match = re.search(r'(\d+)%', clause.clause_text)
            if percentage_match:
                percentage = int(percentage_match.group(1))
                if percentage > 20:
                    risk_indicators.append(f"High penalty rate: {percentage}%")
        
        elif clause.clause_type == ClauseType.NON_COMPETE:
            # Look for duration
            duration_match = re.search(r'(\d+)\s*(?:year|month|day)', clause.clause_text)
            if duration_match:
                duration = int(duration_match.group(1))
                if duration > 2:
                    risk_indicators.append(f"Long non-compete duration: {duration} years")
        
        return risk_indicators
    
    def _identify_compliance_flags(self, clause: ClauseExtractionResult) -> List[str]:
        """Identify compliance-related flags"""
        compliance_flags = []
        text_lower = clause.clause_text.lower()
        
        if clause.clause_type == ClauseType.EXPORT_CONTROL:
            if "restricted" in text_lower or "embargo" in text_lower:
                compliance_flags.append("Export restrictions mentioned")
            if "compliance" in text_lower:
                compliance_flags.append("Compliance requirements specified")
        
        elif clause.clause_type == ClauseType.GOVERNING_LAW:
            if "california" in text_lower or "new york" in text_lower:
                compliance_flags.append("State-specific law jurisdiction")
        
        return compliance_flags
    
    def _assess_business_impact(self, clause: ClauseExtractionResult) -> Dict[str, Any]:
        """Assess the business impact of a clause"""
        impact = {
            "severity": "low",
            "areas_affected": [],
            "mitigation_required": False
        }
        
        # Assess based on clause type and content
        if clause.clause_type == ClauseType.EXCLUSIVITY:
            impact["severity"] = "medium"
            impact["areas_affected"] = ["Business flexibility", "Supplier options"]
            impact["mitigation_required"] = True
        
        elif clause.clause_type == ClauseType.LIQUIDATED_DAMAGES:
            if clause.metadata.get("risk_indicators"):
                impact["severity"] = "high"
                impact["areas_affected"] = ["Financial risk", "Contract performance"]
                impact["mitigation_required"] = True
        
        return impact
    
    async def search_clauses_by_type(
        self,
        clause_type: ClauseType,
        search_text: Optional[str] = None,
        risk_level: Optional[str] = None
    ) -> List[ClauseExtractionResult]:
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
