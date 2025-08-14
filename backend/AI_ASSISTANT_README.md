# AI Assistant - Natural Language Interface

This module implements the Natural Language Interface & Lightweight Orchestrator for Phase 1 of the Supplero project.

## Overview

The AI Assistant provides natural language query processing with intent recognition and parameter extraction, routing queries to appropriate tools with >90% accuracy.

## Features

### 1. Intent Recognition & Query Processing
- **SEARCH_CONTRACTS**: Find contracts by supplier, amount, date, document type, tags
- **GET_DETAILS**: Retrieve detailed information about specific documents
- **EXPORT**: Export contract data in various formats (CSV, JSON, PDF)

### 2. Natural Language Understanding
- Uses OpenAI GPT-4 for intent classification
- Extracts structured parameters from natural language
- Provides confidence scoring for each classification
- Fallback keyword-based parsing if AI fails

### 3. Tool Registry & Orchestration
- Centralized management of available tools
- Intelligent tool selection based on intent
- Parameter validation and transformation
- Execution time tracking and logging

## API Endpoints

### POST `/api/v1/ai-assistant/query`
Process a natural language query and return intent classification.

**Request:**
```json
{
  "query": "Find contracts with supplier ABC Corp over $100,000",
  "user_context": {}
}
```

**Response:**
```json
{
  "query_id": "query_123_4567",
  "original_query": "Find contracts with supplier ABC Corp over $100,000",
  "intent": "SEARCH_CONTRACTS",
  "confidence": 0.95,
  "parameters": {
    "supplier": "ABC Corp",
    "amount_min": 100000
  },
  "confidence_threshold_met": true,
  "suggested_actions": [
    "Execute search with extracted parameters",
    "Modify search criteria if needed",
    "View search results"
  ],
  "error_message": null
}
```

### POST `/api/v1/ai-assistant/execute`
Execute the appropriate tool based on identified intent.

**Request:** Same as query endpoint

**Response:**
```json
{
  "query_id": "exec_123_4567",
  "original_query": "Find contracts with supplier ABC Corp over $100,000",
  "intent": "SEARCH_CONTRACTS",
  "confidence": 0.95,
  "tool_executed": "SEARCH_CONTRACTS",
  "execution_result": {
    "message": "Contract search executed",
    "parameters_used": {...},
    "results_count": 5,
    "search_criteria": {...}
  },
  "execution_time_ms": 245.67,
  "success": true,
  "error_message": null
}
```

### GET `/api/v1/ai-assistant/tools`
Get information about available tools and their capabilities.

**Response:**
```json
{
  "tools": {
    "SEARCH_CONTRACTS": {
      "name": "SEARCH_CONTRACTS",
      "description": "Search for contracts based on various criteria...",
      "parameters": {...},
      "examples": [...]
    }
  },
  "total_tools": 3,
  "user_role": "procurement_manager",
  "organization_id": 1
}
```

## Usage Examples

### Example 1: Contract Search
**Query:** "Show me all contracts with supplier XYZ Corp from last year over $50,000"

**Intent:** SEARCH_CONTRACTS
**Parameters:**
- supplier: "XYZ Corp"
- date_from: "2023-01-01"
- date_to: "2023-12-31"
- amount_min: 50000

### Example 2: Document Details
**Query:** "Get full details for contract ABC-123 including text content"

**Intent:** GET_DETAILS
**Parameters:**
- document_id: "ABC-123"
- include_text: true
- include_metadata: true

### Example 3: Data Export
**Query:** "Export all high-risk contracts to PDF format"

**Intent:** EXPORT
**Parameters:**
- format: "pdf"
- filters: {"risk_level": "high"}

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENAI_MODEL`: Model to use (default: "gpt-4")
- `OPENAI_MAX_TOKENS`: Maximum tokens for responses (default: 4000)
- `OPENAI_TEMPERATURE`: Response randomness (default: 0.1)

### Confidence Threshold
The system requires >90% confidence for intent recognition. Queries below this threshold will return an error message asking the user to rephrase.

## Testing

Run the test script to verify functionality:

```bash
cd backend
python test_ai_assistant.py
```

Make sure to set your `OPENAI_API_KEY` environment variable first.

## Architecture

```
Natural Language Query
         ↓
   Intent Recognition (OpenAI)
         ↓
   Parameter Extraction (OpenAI)
         ↓
   Tool Selection & Routing
         ↓
   Tool Execution
         ↓
   Response Generation
```

## Performance Targets

- **Response Time**: <2s for complex queries
- **Accuracy**: >90% intent recognition
- **Parameter Parsing**: >80% accuracy
- **Tool Execution**: <500ms for simple operations

## Future Enhancements (Phase 2-3)

- Multi-tool query processing
- Context-aware conversations
- Advanced tool orchestration
- Learning from user feedback
- Integration with more sophisticated AI frameworks if needed

## Error Handling

The system gracefully handles:
- OpenAI API failures (fallback to keyword parsing)
- Low confidence classifications
- Invalid parameters
- Tool execution failures
- Network timeouts

All errors are logged with structured logging for monitoring and debugging.





