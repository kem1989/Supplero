# Suppliers-Contracts Relationship Feature

## Overview

The Suppliers-Contracts Relationship Feature enables users to query supplier and contract data using natural language, with AI-powered intent classification and parameter extraction. This feature bridges the gap between supplier management and contract analysis, providing comprehensive insights into supplier-contract relationships.

## Features

### 1. Natural Language Querying
Users can ask complex questions in plain English, such as:
- "Show me suppliers with contracts over $5 million"
- "Find suppliers with service contracts in technology"
- "Suppliers with contracts expiring in 30 days"
- "High-value contract suppliers in manufacturing"

### 2. AI-Powered Intent Classification
The system automatically classifies user queries into specific intent types:
- `SUPPLIERS_BY_CONTRACT_VALUE` - Find suppliers based on contract value criteria
- `SUPPLIERS_WITH_CONTRACT_CRITERIA` - Find suppliers meeting specific contract criteria
- `CONTRACTS_BY_SUPPLIER_CRITERIA` - Find contracts meeting specific supplier criteria
- `SUPPLIER_CONTRACT_PORTFOLIO` - Generate comprehensive portfolio views

### 3. Intelligent Parameter Extraction
Automatically extracts relevant parameters from natural language:
- Contract values (min/max, ranges)
- Supplier criteria (industry, country, risk level)
- Contract criteria (status, type, payment terms)
- Geographic and temporal filters

### 4. Hybrid Search Approach
- **Structured Queries**: When intent is clear, translates to structured database queries
- **RAG Fallback**: When intent is ambiguous, combines extracted text with semantic search via OpenAI
- **Performance Optimization**: Balances accuracy with search performance

## Architecture

### Backend Components

#### 1. Intent Classifier (`IntentClassifier`)
- Uses OpenAI to classify natural language queries
- Supports 20+ intent types including the new supplier-contract relationship intents
- Provides confidence scores and reasoning

#### 2. Parameter Extractor (`ParameterExtractor`)
- Extracts structured parameters from natural language
- Intent-specific extraction rules
- Parameter validation and cleaning

#### 3. Cross-System Handlers
- `execute_suppliers_by_contract_value()` - Contract value-based supplier search
- `execute_suppliers_with_contract_criteria()` - Contract criteria-based supplier search
- `execute_supplier_contract_portfolio()` - Portfolio analysis

#### 4. Cross-System Search Service
- Handles complex queries spanning suppliers and contracts
- Supports multiple query types and filters
- Provides aggregated insights and recommendations

### Frontend Components

#### 1. Enhanced SupplierDiscovery Component
- Natural language search interface
- Example queries for common use cases
- Advanced search filters
- Results display with insights and statistics

#### 2. API Integration
- Unified AI assistant endpoint (`/ai-assistant/execute`)
- Automatic routing to appropriate handlers
- Response transformation and display

## Usage Examples

### Basic Contract Value Queries
```typescript
// Frontend query
const query = "Show me suppliers with contracts over $5 million";

// Backend automatically:
// 1. Classifies as SUPPLIERS_BY_CONTRACT_VALUE
// 2. Extracts contract_value_min: 5000000
// 3. Executes structured database query
// 4. Returns suppliers with contract statistics
```

### Complex Relationship Queries
```typescript
// Frontend query
const query = "Find suppliers with service contracts in technology over $1M in Europe";

// Backend automatically:
// 1. Classifies as SUPPLIERS_WITH_CONTRACT_CRITERIA
// 2. Extracts multiple parameters:
//    - contract_type: "service"
//    - supplier_industry: "technology"
//    - contract_value_min: 1000000
//    - supplier_country: "Europe"
// 3. Executes cross-system search
// 4. Returns filtered results with insights
```

## API Endpoints

### AI Assistant Execute
```
POST /api/v1/ai-assistant/execute
```

**Request Body:**
```json
{
  "query": "Show me suppliers with contracts over $5 million",
  "context": "supplier_search"
}
```

**Response:**
```json
{
  "tool_name": "SUPPLIERS_BY_CONTRACT_VALUE",
  "result": {
    "success": true,
    "message": "Found 15 suppliers with contracts matching value criteria",
    "data": {
      "search_results": {
        "suppliers": [...],
        "statistics": {...}
      }
    }
  }
}
```

## Database Schema

### Key Relationships
- **Supplier** ↔ **Document** (via `supplier_name` in metadata)
- **Document** ↔ **ContractClause** (via `contract_id`)
- **Contract Value** stored in `Document.extracted_metadata.contract_amount`

### Query Optimization
- Uses SQLAlchemy joins for efficient cross-table queries
- Implements pagination for large result sets
- Aggregates contract statistics per supplier

## Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo
```

### Intent Classification Thresholds
```python
CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence for intent classification
FALLBACK_THRESHOLD = 0.5    # Threshold for RAG fallback
```

## Testing

### Test Script
Run the comprehensive test suite:
```bash
cd backend
python test_supplier_contract_relationships.py
```

### Test Coverage
- Intent classification accuracy
- Parameter extraction precision
- Handler execution
- End-to-end AI assistant integration

## Performance Considerations

### Query Optimization
- Database indexes on frequently queried fields
- Query result caching for repeated searches
- Pagination to limit result set sizes

### AI Service Optimization
- Async processing for multiple concurrent queries
- Request batching for parameter extraction
- Fallback mechanisms for service failures

## Security Features

### Access Control
- User authentication required for all queries
- Organization-level data isolation
- Audit logging for all search operations

### Data Privacy
- Sensitive contract data redaction
- User permission-based result filtering
- Secure parameter handling

## Future Enhancements

### Planned Features
1. **Advanced Analytics**: Trend analysis and predictive modeling
2. **Contract Lifecycle Management**: Expiry tracking and renewal alerts
3. **Risk Scoring**: Dynamic risk assessment based on contract terms
4. **Integration APIs**: Third-party supplier and contract data sources

### Scalability Improvements
1. **Elasticsearch Integration**: Full-text search capabilities
2. **Graph Database**: Complex relationship mapping
3. **Real-time Updates**: Live contract and supplier data
4. **Machine Learning**: Improved intent classification accuracy

## Troubleshooting

### Common Issues

#### 1. Intent Classification Failures
- Check OpenAI API key and quota
- Verify query clarity and specificity
- Review intent classification prompts

#### 2. Parameter Extraction Errors
- Ensure query contains extractable parameters
- Check parameter validation rules
- Verify intent type compatibility

#### 3. Search Performance Issues
- Review database query optimization
- Check result set sizes and pagination
- Monitor AI service response times

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

### Development Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables
4. Run tests: `python test_supplier_contract_relationships.py`

### Code Standards
- Follow PEP 8 for Python code
- Use TypeScript for frontend components
- Include comprehensive docstrings
- Write unit tests for new features

## Support

For technical support or feature requests:
- Create an issue in the repository
- Contact the development team
- Review the troubleshooting guide

---

**Version**: 1.0.0  
**Last Updated**: December 2024  
**Maintainer**: Development Team

