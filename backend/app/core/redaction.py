"""
Data redaction service for prompt/output redaction policies and secure storage controls.
Implements enterprise-grade data protection for sensitive information.
"""

import re
import hashlib
import json
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from app.core.config import settings


class RedactionLevel(Enum):
    """Redaction levels for different sensitivity requirements."""
    NONE = "none"
    LOW = "low"           # Basic PII
    MEDIUM = "medium"     # Financial data, contracts
    HIGH = "high"         # Legal documents, sensitive contracts
    CRITICAL = "critical" # Trade secrets, classified information


@dataclass
class RedactionRule:
    """Configuration for a redaction rule."""
    pattern: str
    replacement: str
    description: str
    sensitivity_level: RedactionLevel
    enabled: bool = True


class DataRedactor:
    """Enterprise-grade data redaction service."""
    
    def __init__(self):
        self.rules = self._initialize_rules()
        self.sensitive_patterns = self._initialize_sensitive_patterns()
    
    def _initialize_rules(self) -> List[RedactionRule]:
        """Initialize redaction rules based on enterprise requirements."""
        return [
            # Personal Identifiable Information (PII)
            RedactionRule(
                pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                replacement='[EMAIL_REDACTED]',
                description='Email addresses',
                sensitivity_level=RedactionLevel.LOW
            ),
            RedactionRule(
                pattern=r'\b\d{3}-\d{2}-\d{4}\b',
                replacement='[SSN_REDACTED]',
                description='Social Security Numbers',
                sensitivity_level=RedactionLevel.HIGH
            ),
            RedactionRule(
                pattern=r'\b\d{3}-\d{3}-\d{4}\b',
                replacement='[PHONE_REDACTED]',
                description='Phone numbers',
                sensitivity_level=RedactionLevel.LOW
            ),
            
            # Financial Information
            RedactionRule(
                pattern=r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?',
                replacement='[AMOUNT_REDACTED]',
                description='Monetary amounts',
                sensitivity_level=RedactionLevel.MEDIUM
            ),
            RedactionRule(
                pattern=r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
                replacement='[CARD_REDACTED]',
                description='Credit card numbers',
                sensitivity_level=RedactionLevel.HIGH
            ),
            RedactionRule(
                pattern=r'\b\d{9}\b',
                replacement='[ACCOUNT_REDACTED]',
                description='Bank account numbers',
                sensitivity_level=RedactionLevel.HIGH
            ),
            
            # Legal and Contract Information
            RedactionRule(
                pattern=r'\b(?:confidential|proprietary|trade\s+secret|classified)\b',
                replacement='[SENSITIVE_TERM_REDACTED]',
                description='Sensitive legal terms',
                sensitivity_level=RedactionLevel.CRITICAL
            ),
            RedactionRule(
                pattern=r'\b(?:NDA|non-disclosure|confidentiality)\b',
                replacement='[LEGAL_TERM_REDACTED]',
                description='Legal agreement terms',
                sensitivity_level=RedactionLevel.HIGH
            ),
            
            # Business Information
            RedactionRule(
                pattern=r'\b(?:revenue|profit|margin|EBITDA|EBIT)\b',
                replacement='[FINANCIAL_METRIC_REDACTED]',
                description='Financial metrics',
                sensitivity_level=RedactionLevel.MEDIUM
            ),
            RedactionRule(
                pattern=r'\b(?:customer|client|vendor|supplier)\s+list\b',
                replacement='[BUSINESS_LIST_REDACTED]',
                description='Business relationship lists',
                sensitivity_level=RedactionLevel.HIGH
            ),
            
            # API Keys and Tokens
            RedactionRule(
                pattern=r'\b(?:sk-|pk_|Bearer\s+)[A-Za-z0-9]{20,}\b',
                replacement='[API_KEY_REDACTED]',
                description='API keys and tokens',
                sensitivity_level=RedactionLevel.CRITICAL
            ),
            
            # IP Addresses (internal)
            RedactionRule(
                pattern=r'\b(?:10\.|172\.(?:1[6-9]|2[0-9]|3[01])\.|192\.168\.)\d{1,3}\.\d{1,3}\b',
                replacement='[INTERNAL_IP_REDACTED]',
                description='Internal IP addresses',
                sensitivity_level=RedactionLevel.MEDIUM
            ),
        ]
    
    def _initialize_sensitive_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for different types of sensitive data."""
        return {
            'contract_terms': [
                'payment terms', 'delivery schedule', 'penalty clauses',
                'termination conditions', 'liability limits', 'indemnification'
            ],
            'financial_data': [
                'pricing', 'cost structure', 'profit margins', 'revenue',
                'budget', 'forecast', 'financial projections'
            ],
            'legal_clauses': [
                'force majeure', 'governing law', 'dispute resolution',
                'arbitration', 'jurisdiction', 'legal remedies'
            ],
            'business_strategy': [
                'market position', 'competitive advantage', 'growth strategy',
                'expansion plans', 'acquisition targets', 'partnership strategy'
            ]
        }
    
    def redact_text(
        self, 
        text: str, 
        level: RedactionLevel = RedactionLevel.MEDIUM,
        custom_rules: Optional[List[RedactionRule]] = None
    ) -> str:
        """
        Redact sensitive information from text based on sensitivity level.
        
        Args:
            text: Input text to redact
            level: Minimum sensitivity level to apply redactions
            custom_rules: Additional custom redaction rules
            
        Returns:
            Redacted text with sensitive information replaced
        """
        if not text:
            return text
        
        redacted_text = text
        all_rules = self.rules + (custom_rules or [])
        
        # Apply redaction rules based on sensitivity level
        for rule in all_rules:
            if rule.enabled and rule.sensitivity_level.value >= level.value:
                redacted_text = re.sub(
                    rule.pattern, 
                    rule.replacement, 
                    redacted_text, 
                    flags=re.IGNORECASE
                )
        
        return redacted_text
    
    def redact_json(
        self, 
        data: Union[Dict, List], 
        level: RedactionLevel = RedactionLevel.MEDIUM,
        sensitive_keys: Optional[List[str]] = None
    ) -> Union[Dict, List]:
        """
        Redact sensitive information from JSON data structures.
        
        Args:
            data: JSON data to redact
            level: Minimum sensitivity level to apply redactions
            sensitive_keys: Additional keys to consider sensitive
            
        Returns:
            Redacted JSON data
        """
        if sensitive_keys is None:
            sensitive_keys = []
        
        # Add common sensitive keys
        default_sensitive_keys = [
            'password', 'token', 'secret', 'key', 'credential',
            'ssn', 'social_security', 'credit_card', 'bank_account',
            'salary', 'compensation', 'revenue', 'profit', 'margin'
        ]
        all_sensitive_keys = list(set(sensitive_keys + default_sensitive_keys))
        
        def _redact_value(value: Any, key: str = "") -> Any:
            """Recursively redact values in JSON structures."""
            if isinstance(value, dict):
                return {
                    k: _redact_value(v, k) 
                    for k, v in value.items()
                }
            elif isinstance(value, list):
                return [_redact_value(item, key) for item in value]
            elif isinstance(value, str):
                # Check if the key suggests sensitive content
                is_sensitive_key = any(
                    sensitive in key.lower() 
                    for sensitive in all_sensitive_keys
                )
                
                if is_sensitive_key:
                    return self._get_redaction_replacement(key, value)
                else:
                    return self.redact_text(value, level)
            else:
                return value
        
        return _redact_value(data)
    
    def _get_redaction_replacement(self, key: str, value: str) -> str:
        """Get appropriate redaction replacement based on key and value."""
        key_lower = key.lower()
        
        if any(term in key_lower for term in ['password', 'secret', 'token', 'key']):
            return '[CREDENTIAL_REDACTED]'
        elif any(term in key_lower for term in ['email', 'mail']):
            return '[EMAIL_REDACTED]'
        elif any(term in key_lower for term in ['phone', 'tel', 'mobile']):
            return '[PHONE_REDACTED]'
        elif any(term in key_lower for term in ['ssn', 'social']):
            return '[SSN_REDACTED]'
        elif any(term in key_lower for term in ['card', 'credit', 'bank']):
            return '[FINANCIAL_REDACTED]'
        elif any(term in key_lower for term in ['amount', 'price', 'cost', 'revenue']):
            return '[AMOUNT_REDACTED]'
        else:
            return '[SENSITIVE_DATA_REDACTED]'
    
    def redact_prompt(
        self, 
        prompt: str, 
        level: RedactionLevel = RedactionLevel.MEDIUM
    ) -> str:
        """
        Redact sensitive information from AI prompts.
        
        Args:
            prompt: AI prompt text to redact
            level: Minimum sensitivity level to apply redactions
            
        Returns:
            Redacted prompt text
        """
        # Additional prompt-specific redaction rules
        prompt_rules = [
            RedactionRule(
                pattern=r'\b(?:password|secret|token|key|credential)\s*[:=]\s*\S+',
                replacement='[CREDENTIAL_REDACTED]',
                description='Credential patterns in prompts',
                sensitivity_level=RedactionLevel.CRITICAL
            ),
            RedactionRule(
                pattern=r'\b(?:analyze|review|examine)\s+(?:this|the)\s+(?:contract|document|agreement)\b',
                replacement='[DOCUMENT_REFERENCE_REDACTED]',
                description='Document reference patterns',
                sensitivity_level=RedactionLevel.MEDIUM
            ),
        ]
        
        return self.redact_text(prompt, level, prompt_rules)
    
    def redact_ai_response(
        self, 
        response: str, 
        level: RedactionLevel = RedactionLevel.MEDIUM
    ) -> str:
        """
        Redact sensitive information from AI responses.
        
        Args:
            response: AI response text to redact
            level: Minimum sensitivity level to apply redactions
            
        Returns:
            Redacted response text
        """
        # Additional response-specific redaction rules
        response_rules = [
            RedactionRule(
                pattern=r'\b(?:Based on the|According to the|The document shows)\s+[^.]*',
                replacement='[ANALYSIS_CONTEXT_REDACTED]',
                description='Analysis context patterns',
                sensitivity_level=RedactionLevel.MEDIUM
            ),
            RedactionRule(
                pattern=r'\b(?:I found|I detected|I identified)\s+[^.]*',
                replacement='[AI_INSIGHT_REDACTED]',
                description='AI insight patterns',
                sensitivity_level=RedactionLevel.MEDIUM
            ),
        ]
        
        return self.redact_text(response, level, response_rules)
    
    def create_redaction_summary(
        self, 
        original: str, 
        redacted: str
    ) -> Dict[str, Any]:
        """
        Create a summary of what was redacted.
        
        Args:
            original: Original text
            redacted: Redacted text
            
        Returns:
            Summary of redaction operations
        """
        # Count redaction patterns
        redaction_patterns = re.findall(r'\[([^\]]+)_REDACTED\]', redacted)
        pattern_counts = {}
        
        for pattern in redaction_patterns:
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        return {
            'original_length': len(original),
            'redacted_length': len(redacted),
            'redaction_count': len(redaction_patterns),
            'redaction_types': pattern_counts,
            'redaction_ratio': len(redaction_patterns) / max(len(original), 1)
        }
    
    def is_sensitive_content(self, text: str, threshold: float = 0.1) -> bool:
        """
        Determine if content contains sensitive information.
        
        Args:
            text: Text to analyze
            threshold: Minimum ratio of sensitive patterns to consider content sensitive
            
        Returns:
            True if content is considered sensitive
        """
        if not text:
            return False
        
        # Count sensitive patterns
        sensitive_count = 0
        for rule in self.rules:
            if rule.enabled:
                matches = re.findall(rule.pattern, text, flags=re.IGNORECASE)
                sensitive_count += len(matches)
        
        ratio = sensitive_count / max(len(text.split()), 1)
        return ratio >= threshold


# Global redactor instance
redactor = DataRedactor()


def get_redactor() -> DataRedactor:
    """Get the global redactor instance."""
    return redactor


def redact_for_logging(
    data: Any, 
    level: RedactionLevel = RedactionLevel.MEDIUM
) -> Any:
    """
    Convenience function to redact data for logging purposes.
    
    Args:
        data: Data to redact
        level: Redaction sensitivity level
        
    Returns:
        Redacted data safe for logging
    """
    if isinstance(data, str):
        return redactor.redact_text(data, level)
    elif isinstance(data, (dict, list)):
        return redactor.redact_json(data, level)
    else:
        return data


def redact_for_audit(
    data: Any, 
    level: RedactionLevel = RedactionLevel.HIGH
) -> Any:
    """
    Convenience function to redact data for audit logging.
    
    Args:
        data: Data to redact
        level: Redaction sensitivity level (defaults to HIGH for audit)
        
    Returns:
        Redacted data safe for audit logging
    """
    return redact_for_logging(data, level) 