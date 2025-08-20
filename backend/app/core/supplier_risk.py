"""
Supplier risk assessment service for basic risk scoring and analysis.
"""

import structlog
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.schemas.supplier import RiskLevel, CompanySize
from app.core.external_data_aggregation import ExternalDataAggregationService

logger = structlog.get_logger(__name__)


class SupplierRiskService:
    """Service for assessing supplier risk using rule-based logic."""
    
    # Industry risk factors (higher values = higher risk)
    INDUSTRY_RISK_FACTORS = {
        "pharmaceuticals": 0.3,
        "healthcare": 0.25,
        "financial_services": 0.4,
        "banking": 0.4,
        "manufacturing": 0.2,
        "automotive": 0.15,
        "technology": 0.1,
        "retail": 0.1,
        "food_beverage": 0.2,
        "energy": 0.3,
        "construction": 0.25,
        "aviation": 0.35,
        "defense": 0.5,
        "telecommunications": 0.2,
        "logistics": 0.15,
        "consulting": 0.05,
        "education": 0.05,
        "non_profit": 0.1
    }
    
    # Company size risk factors (smaller companies = higher risk)
    SIZE_RISK_FACTORS = {
        CompanySize.SMALL: 0.3,
        CompanySize.MEDIUM: 0.15,
        CompanySize.LARGE: 0.05,
        CompanySize.ENTERPRISE: 0.0
    }
    
    # Country risk factors (simplified - in production would use external data)
    COUNTRY_RISK_FACTORS = {
        "US": 0.0,
        "CA": 0.05,
        "GB": 0.05,
        "DE": 0.05,
        "FR": 0.05,
        "JP": 0.05,
        "AU": 0.05,
        "SG": 0.05,
        "CH": 0.05,
        "NL": 0.05,
        "SE": 0.05,
        "NO": 0.05,
        "DK": 0.05,
        "FI": 0.05,
        "NZ": 0.05,
        # Higher risk countries (keys must be uppercase to match the lookup logic)
        "CHINA": 0.4,
        "CN": 0.4,
        "RUSSIA": 0.6,
        "RU": 0.6,
        "IRAN": 0.8,
        "IR": 0.8,
        "NORTH KOREA": 0.9,
        "KP": 0.9,
        "SYRIA": 0.7,
        "SY": 0.7,
        "VENEZUELA": 0.5,
        "VE": 0.5,
        "BELARUS": 0.5,
        "BY": 0.5,
        "MYANMAR": 0.6,
        "MM": 0.6
    }
    
    @classmethod
    def calculate_basic_risk_score(
        cls,
        industry: Optional[str] = None,
        company_size: Optional[CompanySize] = None,
        country: Optional[str] = None,
        employee_count: Optional[int] = None,
        revenue_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate basic risk score based on supplier profile information.
        
        Returns:
            Dict containing risk_score, risk_level, and risk_factors
        """
        base_score = 0.0
        risk_factors = {}
        
        # Industry risk assessment
        if industry:
            industry_lower = industry.lower().replace(" ", "_")
            industry_risk = cls.INDUSTRY_RISK_FACTORS.get(industry_lower, 0.15)
            base_score += industry_risk * 60  # Industry contributes up to 60 points
            risk_factors["industry_risk"] = {
                "industry": industry,
                "risk_factor": industry_risk,
                "contribution": industry_risk * 60
            }
        
        # Company size risk assessment
        if company_size:
            size_risk = cls.SIZE_RISK_FACTORS.get(company_size, 0.15)
            base_score += size_risk * 25  # Size contributes up to 25 points
            risk_factors["size_risk"] = {
                "company_size": company_size,
                "risk_factor": size_risk,
                "contribution": size_risk * 25
            }
        
        # Country risk assessment
        if country:
            country_upper = country.upper()
            country_risk = cls.COUNTRY_RISK_FACTORS.get(country_upper, 0.2)
            base_score += country_risk * 40  # Country contributes up to 40 points
            risk_factors["country_risk"] = {
                "country": country,
                "risk_factor": country_risk,
                "contribution": country_risk * 40
            }
        
        # Employee count risk (smaller companies = higher risk)
        if employee_count:
            if employee_count < 10:
                emp_risk = 0.4
            elif employee_count < 50:
                emp_risk = 0.3
            elif employee_count < 200:
                emp_risk = 0.2
            elif employee_count < 1000:
                emp_risk = 0.1
            else:
                emp_risk = 0.05
            
            base_score += emp_risk * 15  # Employee count contributes up to 15 points
            risk_factors["employee_risk"] = {
                "employee_count": employee_count,
                "risk_factor": emp_risk,
                "contribution": emp_risk * 15
            }
        
        # Revenue risk (lower revenue = higher risk)
        if revenue_range:
            revenue_risk = cls._assess_revenue_risk(revenue_range)
            base_score += revenue_risk * 10  # Revenue contributes up to 10 points
            risk_factors["revenue_risk"] = {
                "revenue_range": revenue_range,
                "risk_factor": revenue_risk,
                "contribution": revenue_risk * 10
            }
        
        # Data completeness penalty
        data_completeness_score = cls._assess_data_completeness(
            industry, company_size, country, employee_count, revenue_range
        )
        base_score += data_completeness_score
        
        # Ensure score is within 0-100 range
        final_score = max(0.0, min(100.0, base_score))
        
        # Determine risk level
        risk_level = cls._determine_risk_level(final_score)
        
        # Add assessment metadata
        risk_factors["assessment_metadata"] = {
            "assessment_date": datetime.utcnow().isoformat(),
            "assessment_method": "rule_based",
            "data_completeness_score": data_completeness_score,
            "base_score": base_score,
            "final_score": final_score
        }
        
        logger.info(
            "Risk assessment completed",
            final_score=final_score,
            risk_level=risk_level,
            risk_factors=risk_factors
        )
        
        return {
            "risk_score": final_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors
        }
    
    @classmethod
    def _assess_revenue_risk(cls, revenue_range: str) -> float:
        """Assess risk based on revenue range."""
        revenue_lower = revenue_range.lower()
        
        if "under" in revenue_lower or "less than" in revenue_lower:
            return 0.4
        elif "1m" in revenue_lower or "million" in revenue_lower:
            if "under" in revenue_lower or "less than" in revenue_lower:
                return 0.3
            else:
                return 0.2
        elif "10m" in revenue_lower or "10 million" in revenue_lower:
            return 0.15
        elif "100m" in revenue_lower or "100 million" in revenue_lower:
            return 0.1
        elif "1b" in revenue_lower or "billion" in revenue_lower:
            return 0.05
        else:
            return 0.2  # Default moderate risk
    
    @classmethod
    def _assess_data_completeness(
        cls,
        industry: Optional[str],
        company_size: Optional[CompanySize],
        country: Optional[str],
        employee_count: Optional[int],
        revenue_range: Optional[str]
    ) -> float:
        """Assess risk based on data completeness."""
        provided_fields = sum([
            1 if industry else 0,
            1 if company_size else 0,
            1 if country else 0,
            1 if employee_count else 0,
            1 if revenue_range else 0
        ])
        
        # Penalty for missing data (up to 10 points)
        completeness_penalty = (5 - provided_fields) * 2
        return max(0, completeness_penalty)
    
    @classmethod
    def _determine_risk_level(cls, risk_score: float) -> str:
        """Determine risk level based on score."""
        if risk_score >= 80:
            return RiskLevel.CRITICAL
        elif risk_score >= 60:
            return RiskLevel.HIGH
        elif risk_score >= 40:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    @classmethod
    def generate_recommendations(
        cls,
        risk_score: float,
        risk_factors: Dict[str, Any],
        industry: Optional[str] = None
    ) -> List[str]:
        """Generate recommendations based on risk assessment."""
        recommendations = []
        
        if risk_score > 70:
            recommendations.append("High risk supplier - recommend immediate review and monitoring")
            recommendations.append("Consider adding to watchlist for continuous monitoring")
        
        elif risk_score > 50:
            recommendations.append("Medium risk supplier - recommend enhanced due diligence")
            recommendations.append("Consider quarterly risk reviews")
        
        elif risk_score > 30:
            recommendations.append("Low-medium risk - recommend annual risk reviews")
        
        # Industry-specific recommendations
        if industry:
            if industry.lower() in ["pharmaceuticals", "healthcare"]:
                recommendations.append("Healthcare supplier - ensure FDA compliance verification")
            elif industry.lower() in ["financial_services", "banking"]:
                recommendations.append("Financial services supplier - verify regulatory compliance")
            elif industry.lower() in ["defense", "aviation"]:
                recommendations.append("Defense/Aviation supplier - verify security clearances")
        
        # Data completeness recommendations
        if risk_factors.get("assessment_metadata", {}).get("data_completeness_score", 0) > 0:
            recommendations.append("Incomplete supplier data - recommend gathering additional information")
        
        return recommendations
    
    @classmethod
    async def calculate_enhanced_risk_score(
        cls,
        supplier_name: str,
        industry: Optional[str] = None,
        company_size: Optional[CompanySize] = None,
        country: Optional[str] = None,
        employee_count: Optional[int] = None,
        revenue_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate enhanced risk score using external data sources.
        
        This method combines basic risk scoring with external data aggregation
        to provide a more comprehensive risk assessment.
        """
        try:
            # Get basic risk score first
            basic_risk = cls.calculate_basic_risk_score(
                industry=industry,
                company_size=company_size,
                country=country,
                employee_count=employee_count,
                revenue_range=revenue_range
            )
            
            # Aggregate external data
            external_data_service = ExternalDataAggregationService()
            external_data = await external_data_service.aggregate_supplier_risk_data(
                supplier_name=supplier_name,
                industry=industry,
                country=country
            )
            
            # Combine basic risk with external data
            enhanced_risk = cls._combine_risk_scores(basic_risk, external_data)
            
            logger.info(
                "Enhanced risk assessment completed",
                supplier_name=supplier_name,
                basic_score=basic_risk["risk_score"],
                enhanced_score=enhanced_risk["risk_score"],
                external_signals=len(external_data.get("risk_signals", []))
            )
            
            return enhanced_risk
            
        except Exception as e:
            logger.error(
                "Failed to calculate enhanced risk score",
                supplier_name=supplier_name,
                error=str(e),
                exc_info=True
            )
            # Fall back to basic risk score
            return cls.calculate_basic_risk_score(
                industry=industry,
                company_size=company_size,
                country=country,
                employee_count=employee_count,
                revenue_range=revenue_range
            )
    
    @classmethod
    def _combine_risk_scores(
        cls,
        basic_risk: Dict[str, Any],
        external_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combine basic risk score with external data risk signals."""
        # Start with basic risk factors
        combined_risk_factors = basic_risk["risk_factors"].copy()
        
        # Add external data risk factors
        external_risk_score = external_data.get("risk_indicators", {}).get("overall_risk_score", 0)
        external_signals = external_data.get("risk_signals", [])
        
        # Calculate external risk contribution
        if external_signals:
            # Count high and critical signals
            high_critical_count = sum(
                1 for signal in external_signals 
                if signal.severity in ["high", "critical"]
            )
            
            # External risk contributes up to 30 points
            external_contribution = min(30, high_critical_count * 10)
            
            combined_risk_factors["external_risk"] = {
                "external_risk_score": external_risk_score,
                "risk_signals_count": len(external_signals),
                "high_critical_signals": high_critical_count,
                "contribution": external_contribution
            }
        else:
            external_contribution = 0
            combined_risk_factors["external_risk"] = {
                "external_risk_score": external_risk_score,
                "risk_signals_count": 0,
                "high_critical_signals": 0,
                "contribution": 0
            }
        
        # Calculate combined score (basic + external, capped at 100)
        combined_score = min(100, basic_risk["risk_score"] + external_contribution)
        
        # Determine new risk level
        combined_risk_level = cls._determine_risk_level(combined_score)
        
        # Add external data summary
        combined_risk_factors["external_data_summary"] = {
            "aggregation_timestamp": external_data.get("aggregation_timestamp"),
            "data_sources": external_data.get("data_sources", []),
            "summary": external_data.get("summary", "No external data available")
        }
        
        return {
            "risk_score": combined_score,
            "risk_level": combined_risk_level,
            "risk_factors": combined_risk_factors,
            "external_data": external_data,
            "assessment_method": "enhanced_with_external_data"
        }
