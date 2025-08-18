"""
External data aggregation service for supplier risk assessment.
Aggregates data from public sources like news APIs, financial data APIs, etc.
"""

import structlog
import httpx
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from app.core.config import settings

logger = structlog.get_logger(__name__)


@dataclass
class NewsArticle:
    """Represents a news article with sentiment analysis."""
    title: str
    description: str
    url: str
    published_at: datetime
    source: str
    sentiment_score: float
    relevance_score: float
    risk_keywords: List[str]


@dataclass
class FinancialData:
    """Represents basic financial health indicators."""
    company_name: str
    credit_rating: Optional[str]
    financial_health_score: Optional[float]
    risk_indicators: List[str]
    last_updated: datetime


@dataclass
class RiskSignal:
    """Represents a risk signal from external data sources."""
    source: str
    signal_type: str  # "news", "financial", "compliance", "industry"
    severity: str  # "low", "medium", "high", "critical"
    description: str
    confidence_score: float
    timestamp: datetime
    metadata: Dict[str, Any]


class ExternalDataAggregationService:
    """Service for aggregating external data to generate supplier risk signals."""
    
    def __init__(self):
        # Import settings directly in the method to avoid any scope issues
        from app.core.config import settings as config_settings
        self.news_api_key = config_settings.NEWS_API_KEY
        self.dun_bradstreet_api_key = config_settings.DUN_BRADSTREET_API_KEY
        self.refinitiv_api_key = config_settings.REFINITIV_API_KEY
        
        # Risk keywords that indicate potential issues
        self.risk_keywords = {
            "financial": [
                "bankruptcy", "insolvency", "liquidation", "receivership", "administration",
                "debt", "default", "credit downgrade", "financial distress", "cash flow problems",
                "layoffs", "restructuring", "cost cutting", "revenue decline", "losses"
            ],
            "compliance": [
                "investigation", "probe", "inquiry", "allegations", "charges", "indictment",
                "settlement", "fine", "penalty", "sanctions", "violations", "breach",
                "regulatory action", "cease and desist", "suspension", "revocation"
            ],
            "operational": [
                "recall", "safety issue", "quality problem", "supply chain disruption",
                "production halt", "facility closure", "equipment failure", "cyber attack",
                "data breach", "system outage", "strike", "labor dispute"
            ],
            "reputation": [
                "scandal", "controversy", "negative publicity", "boycott", "protest",
                "environmental damage", "human rights violation", "corruption", "fraud",
                "misconduct", "ethics violation"
            ]
        }
    
    async def aggregate_supplier_risk_data(
        self,
        supplier_name: str,
        industry: Optional[str] = None,
        country: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Aggregate risk data from multiple external sources for a supplier.
        
        Args:
            supplier_name: Name of the supplier to research
            industry: Industry sector (optional, for context)
            country: Country of operation (optional, for context)
            
        Returns:
            Dictionary containing aggregated risk data and signals
        """
        logger.info(
            "Starting external data aggregation for supplier",
            supplier_name=supplier_name,
            industry=industry,
            country=country
        )
        
        try:
            # Gather data from multiple sources concurrently
            tasks = [
                self._fetch_news_data(supplier_name, industry),
                self._fetch_financial_data(supplier_name),
                self._fetch_industry_risk_data(industry),
                self._fetch_compliance_data(supplier_name, country)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle any exceptions
            news_data = results[0] if not isinstance(results[0], Exception) else []
            financial_data = results[1] if not isinstance(results[1], Exception) else None
            industry_risk = results[2] if not isinstance(results[2], Exception) else {}
            compliance_data = results[3] if not isinstance(results[3], Exception) else []
            
            # Generate risk signals from aggregated data
            risk_signals = self._generate_risk_signals(
                supplier_name, news_data, financial_data, industry_risk, compliance_data
            )
            
            # Calculate overall risk indicators
            risk_indicators = self._calculate_risk_indicators(
                news_data, financial_data, industry_risk, compliance_data
            )
            
            aggregated_data = {
                "supplier_name": supplier_name,
                "aggregation_timestamp": datetime.utcnow().isoformat(),
                "data_sources": self._get_used_data_sources(),
                "news_data": news_data,
                "financial_data": financial_data,
                "industry_risk": industry_risk,
                "compliance_data": compliance_data,
                "risk_signals": risk_signals,
                "risk_indicators": risk_indicators,
                "summary": self._generate_summary(risk_signals, risk_indicators)
            }
            
            logger.info(
                "External data aggregation completed successfully",
                supplier_name=supplier_name,
                signals_count=len(risk_signals),
                risk_score=risk_indicators.get("overall_risk_score", 0)
            )
            
            return aggregated_data
            
        except Exception as e:
            logger.error(
                "Failed to aggregate external data",
                supplier_name=supplier_name,
                error=str(e),
                exc_info=True
            )
            return {
                "supplier_name": supplier_name,
                "error": "Failed to aggregate external data",
                "aggregation_timestamp": datetime.utcnow().isoformat()
            }
    
    async def _fetch_news_data(
        self,
        supplier_name: str,
        industry: Optional[str] = None
    ) -> List[NewsArticle]:
        """Fetch news data from News API."""
        if not self.news_api_key:
            logger.warning("News API key not configured, skipping news data fetch")
            return []
        
        try:
            # Search for company-specific news
            company_query = f'"{supplier_name}"'
            industry_query = f'"{industry}"' if industry else ""
            
            # Combine queries for better results
            search_query = f"{company_query} {industry_query}".strip()
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q": search_query,
                        "apiKey": self.news_api_key,
                        "language": "en",
                        "sortBy": "relevancy",
                        "pageSize": 50,
                        "from": (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get("articles", [])
                    
                    # Process and analyze articles
                    processed_articles = []
                    for article in articles[:20]:  # Limit to top 20 most relevant
                        processed_article = self._process_news_article(article, supplier_name)
                        if processed_article:
                            processed_articles.append(processed_article)
                    
                    logger.info(
                        "News data fetched successfully",
                        supplier_name=supplier_name,
                        articles_found=len(articles),
                        processed_articles=len(processed_articles)
                    )
                    
                    return processed_articles
                else:
                    logger.warning(
                        "News API request failed",
                        status_code=response.status_code,
                        response_text=response.text[:200]
                    )
                    return []
                    
        except Exception as e:
            logger.error(
                "Error fetching news data",
                supplier_name=supplier_name,
                error=str(e),
                exc_info=True
            )
            return []
    
    def _process_news_article(
        self,
        article: Dict[str, Any],
        supplier_name: str
    ) -> Optional[NewsArticle]:
        """Process a raw news article and extract relevant information."""
        try:
            # Calculate relevance score based on title and description
            title = article.get("title", "").lower()
            description = article.get("description", "").lower()
            supplier_lower = supplier_name.lower()
            
            # Check if supplier name appears in title or description
            title_relevance = 1.0 if supplier_lower in title else 0.0
            desc_relevance = 0.8 if supplier_lower in description else 0.0
            
            # Calculate overall relevance
            relevance_score = max(title_relevance, desc_relevance)
            
            if relevance_score < 0.3:  # Skip low-relevance articles
                return None
            
            # Analyze sentiment and identify risk keywords
            sentiment_score = self._analyze_article_sentiment(title, description)
            risk_keywords = self._identify_risk_keywords(title, description)
            
            # Parse publication date
            published_at = datetime.utcnow()
            if article.get("publishedAt"):
                try:
                    published_at = datetime.fromisoformat(
                        article["publishedAt"].replace("Z", "+00:00")
                    )
                except ValueError:
                    pass
            
            return NewsArticle(
                title=article.get("title", ""),
                description=article.get("description", ""),
                url=article.get("url", ""),
                published_at=published_at,
                source=article.get("source", {}).get("name", "Unknown"),
                sentiment_score=sentiment_score,
                relevance_score=relevance_score,
                risk_keywords=risk_keywords
            )
            
        except Exception as e:
            logger.error(
                "Error processing news article",
                article_title=article.get("title", "Unknown"),
                error=str(e)
            )
            return None
    
    def _analyze_article_sentiment(self, title: str, description: str) -> float:
        """Simple sentiment analysis based on risk keywords."""
        text = f"{title} {description}".lower()
        
        # Count positive and negative indicators
        positive_indicators = [
            "growth", "profit", "success", "expansion", "innovation", "award",
            "recognition", "partnership", "investment", "recovery", "improvement"
        ]
        
        negative_indicators = [
            "loss", "decline", "failure", "problem", "issue", "concern",
            "risk", "threat", "challenge", "difficulty", "setback"
        ]
        
        positive_count = sum(1 for word in positive_indicators if word in text)
        negative_count = sum(1 for word in negative_indicators if word in text)
        
        # Calculate sentiment score (-1 to 1, where -1 is very negative)
        if positive_count == 0 and negative_count == 0:
            return 0.0
        
        total = positive_count + negative_count
        sentiment_score = (positive_count - negative_count) / total
        
        return sentiment_score
    
    def _identify_risk_keywords(self, title: str, description: str) -> List[str]:
        """Identify risk-related keywords in article text."""
        text = f"{title} {description}".lower()
        found_keywords = []
        
        for category, keywords in self.risk_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    found_keywords.append(f"{category}:{keyword}")
        
        return found_keywords
    
    async def _fetch_financial_data(self, supplier_name: str) -> Optional[FinancialData]:
        """Fetch basic financial data (placeholder for now)."""
        # This would integrate with financial data providers like:
        # - Dun & Bradstreet
        # - Refinitiv
        # - Bloomberg
        # - Credit rating agencies
        
        if not (self.dun_bradstreet_api_key or self.refinitiv_api_key):
            logger.warning("Financial API keys not configured, using placeholder data")
            return self._generate_placeholder_financial_data(supplier_name)
        
        # TODO: Implement actual financial data API calls
        # For now, return placeholder data
        return self._generate_placeholder_financial_data(supplier_name)
    
    def _generate_placeholder_financial_data(self, supplier_name: str) -> FinancialData:
        """Generate placeholder financial data for development/testing."""
        return FinancialData(
            company_name=supplier_name,
            credit_rating=None,
            financial_health_score=None,
            risk_indicators=["Data not available"],
            last_updated=datetime.utcnow()
        )
    
    async def _fetch_industry_risk_data(self, industry: Optional[str]) -> Dict[str, Any]:
        """Fetch industry-specific risk data."""
        if not industry:
            return {}
        
        # Industry risk factors based on current market conditions
        # In production, this would come from industry research APIs
        industry_risks = {
            "pharmaceuticals": {
                "regulatory_environment": "High",
                "patent_expiration_risk": "Medium",
                "clinical_trial_risk": "High",
                "market_volatility": "Medium"
            },
            "financial_services": {
                "regulatory_environment": "High",
                "interest_rate_risk": "High",
                "credit_risk": "Medium",
                "market_volatility": "High"
            },
            "manufacturing": {
                "supply_chain_risk": "Medium",
                "commodity_price_risk": "Medium",
                "labor_risk": "Low",
                "technology_disruption": "Medium"
            },
            "technology": {
                "rapid_innovation_risk": "High",
                "cybersecurity_risk": "High",
                "talent_retention_risk": "Medium",
                "market_competition": "High"
            }
        }
        
        return industry_risks.get(industry.lower(), {})
    
    async def _fetch_compliance_data(
        self,
        supplier_name: str,
        country: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Fetch compliance and regulatory data."""
        # This would integrate with compliance databases and regulatory APIs
        # For now, return empty list
        return []
    
    def _generate_risk_signals(
        self,
        supplier_name: str,
        news_data: List[NewsArticle],
        financial_data: Optional[FinancialData],
        industry_risk: Dict[str, Any],
        compliance_data: List[Dict[str, Any]]
    ) -> List[RiskSignal]:
        """Generate risk signals from aggregated data."""
        signals = []
        
        # Generate signals from news data
        for article in news_data:
            if article.sentiment_score < -0.3:  # Negative sentiment
                severity = "high" if article.sentiment_score < -0.7 else "medium"
                
                signal = RiskSignal(
                    source="news",
                    signal_type="news",
                    severity=severity,
                    description=f"Negative news: {article.title}",
                    confidence_score=article.relevance_score,
                    timestamp=article.published_at,
                    metadata={
                        "article_url": article.url,
                        "sentiment_score": article.sentiment_score,
                        "risk_keywords": article.risk_keywords,
                        "source": article.source
                    }
                )
                signals.append(signal)
        
        # Generate signals from financial data
        if financial_data and financial_data.risk_indicators:
            for indicator in financial_data.risk_indicators:
                if "not available" not in indicator.lower():
                    signal = RiskSignal(
                        source="financial",
                        signal_type="financial",
                        severity="medium",
                        description=f"Financial risk indicator: {indicator}",
                        confidence_score=0.7,
                        timestamp=financial_data.last_updated,
                        metadata={
                            "indicator": indicator,
                            "financial_health_score": financial_data.financial_health_score
                        }
                    )
                    signals.append(signal)
        
        # Generate signals from industry risk
        for risk_factor, risk_level in industry_risk.items():
            if risk_level in ["High", "Critical"]:
                signal = RiskSignal(
                    source="industry",
                    signal_type="industry",
                    severity=risk_level.lower(),
                    description=f"Industry risk: {risk_factor} - {risk_level}",
                    confidence_score=0.8,
                    timestamp=datetime.utcnow(),
                    metadata={
                        "risk_factor": risk_factor,
                        "risk_level": risk_level
                    }
                )
                signals.append(signal)
        
        return signals
    
    def _calculate_risk_indicators(
        self,
        news_data: List[NewsArticle],
        financial_data: Optional[FinancialData],
        industry_risk: Dict[str, Any],
        compliance_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate overall risk indicators from aggregated data."""
        indicators = {}
        
        # News sentiment risk
        if news_data:
            negative_articles = [a for a in news_data if a.sentiment_score < -0.3]
            news_risk_score = len(negative_articles) / len(news_data) * 100
            indicators["news_risk_score"] = min(100, news_risk_score)
            indicators["negative_news_count"] = len(negative_articles)
            indicators["total_news_count"] = len(news_data)
        
        # Financial health risk
        if financial_data and financial_data.financial_health_score is not None:
            indicators["financial_risk_score"] = (1 - financial_data.financial_health_score) * 100
        
        # Industry risk
        if industry_risk:
            high_risk_factors = sum(1 for level in industry_risk.values() if level in ["High", "Critical"])
            total_factors = len(industry_risk)
            if total_factors > 0:
                indicators["industry_risk_score"] = (high_risk_factors / total_factors) * 100
        
        # Overall risk score (weighted average)
        risk_scores = []
        weights = []
        
        if "news_risk_score" in indicators:
            risk_scores.append(indicators["news_risk_score"])
            weights.append(0.4)  # News has highest weight
        
        if "financial_risk_score" in indicators:
            risk_scores.append(indicators["financial_risk_score"])
            weights.append(0.35)  # Financial data second highest
        
        if "industry_risk_score" in indicators:
            risk_scores.append(indicators["industry_risk_score"])
            weights.append(0.25)  # Industry risk lowest weight
        
        if risk_scores and weights:
            total_weight = sum(weights)
            weighted_scores = [score * weight for score, weight in zip(risk_scores, weights)]
            indicators["overall_risk_score"] = sum(weighted_scores) / total_weight
        else:
            indicators["overall_risk_score"] = 0.0
        
        return indicators
    
    def _get_used_data_sources(self) -> List[str]:
        """Get list of data sources that were actually used."""
        sources = []
        
        if self.news_api_key:
            sources.append("News API")
        
        if self.dun_bradstreet_api_key:
            sources.append("Dun & Bradstreet")
        
        if self.refinitiv_api_key:
            sources.append("Refinitiv")
        
        if not sources:
            sources.append("Placeholder/Development Data")
        
        return sources
    
    def _generate_summary(
        self,
        risk_signals: List[RiskSignal],
        risk_indicators: Dict[str, Any]
    ) -> str:
        """Generate a human-readable summary of the risk assessment."""
        if not risk_signals:
            return "No significant risk signals detected from external sources."
        
        # Count signals by severity
        critical_count = sum(1 for s in risk_signals if s.severity == "critical")
        high_count = sum(1 for s in risk_signals if s.severity == "high")
        medium_count = sum(1 for s in risk_signals if s.severity == "medium")
        
        summary_parts = []
        
        if critical_count > 0:
            summary_parts.append(f"{critical_count} critical risk signal(s)")
        if high_count > 0:
            summary_parts.append(f"{high_count} high risk signal(s)")
        if medium_count > 0:
            summary_parts.append(f"{medium_count} medium risk signal(s)")
        
        overall_score = risk_indicators.get("overall_risk_score", 0)
        
        if overall_score > 70:
            risk_level = "High"
        elif overall_score > 40:
            risk_level = "Medium"
        else:
            risk_level = "Low"
        
        summary_parts.append(f"Overall external risk level: {risk_level}")
        
        return f"Detected {', '.join(summary_parts)}."
