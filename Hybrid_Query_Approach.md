# **Recommended Approach: Extend Multi-Part Query Detection for Hybrid Database + OpenAI Knowledge Queries**

## **Overview**
For hybrid queries that need both database checks AND external knowledge (via OpenAI), extend your existing multi-part query detection system rather than creating new intents.

## **Current State Analysis**

### **Existing Infrastructure (Keep As-Is)**
Your system already has:
- `detect_multi_part_query()` method
- `MultiPartQueryComponent` with component types
- Multi-part query detection prompts
- Handler architecture for different intents

### **Current Component Types**
1. **"retrieval"** - Database queries (SQL_QUERY, SQL_ANALYTICS, COMPARISON_QUERY)
2. **"explanation"** - Explanatory content (GENERATE_EXPLANATION) 
3. **"insights"** - Strategic insights (GENERATE_INSIGHTS)

## **Proposed Changes**

### **1. Add New Component Type**
Extend component types to include:
- **"external_knowledge"** - Questions requiring OpenAI's knowledge base for information outside your database

### **2. Enhanced Multi-Part Detection**
Update your multi-part detection prompt to recognize patterns like:
```
"Find me all suppliers, and then tell me why suppliers in China are different from Suppliers in India in terms of documentation"
```

This would decompose into:
1. **Retrieval component**: "Find me all suppliers" → Database query
2. **External knowledge component**: "tell me why suppliers in China are different from Suppliers in India in terms of documentation" → OpenAI knowledge

### **3. New Handler Architecture**
Add new handler:
- **`EXTERNAL_KNOWLEDGE_HANDLER`** - Makes OpenAI API calls for general knowledge questions
- **`HYBRID_QUERY_HANDLER`** - Orchestrates both database and external knowledge components

### **4. Execution Flow**
```
User Query → Multi-Part Detection → Component Decomposition → 
Parallel Execution:
├── Database Query (existing SQL pipeline)
└── External Knowledge Query (new OpenAI knowledge pipeline)
→ Response Synthesis → Combined Result
```

### **5. Response Formatting**
Extend response formatter to handle hybrid responses with:
- Database results section
- External knowledge results section  
- Synthesized insights combining both

## **Implementation Steps**

### **Step 1: Update Component Types**
```python
# In MultiPartQueryComponent
component_type: str  # "retrieval", "explanation", "insights", or "external_knowledge"
```

### **Step 2: Enhance Multi-Part Detection Prompt**
Update the prompt to include "external_knowledge" in component types:
```
"component_type": "retrieval|explanation|insights|external_knowledge"
```

Add detection rules for external knowledge patterns:
- Questions about general business practices
- Industry comparisons across countries
- Regulatory differences
- Market trends not in your database

### **Step 3: Create External Knowledge Handler**
```python
class ExternalKnowledgeHandler:
    async def execute_external_knowledge_query(self, query_text: str) -> Dict[str, Any]:
        # Make OpenAI API call for general knowledge
        # Return formatted response
```

### **Step 4: Create Hybrid Query Handler**
```python
class HybridQueryHandler:
    async def execute_hybrid_query(self, components: List[MultiPartQueryComponent]) -> Dict[str, Any]:
        # Execute database components
        # Execute external knowledge components  
        # Synthesize results
```

### **Step 5: Update Response Formatting**
Extend response formatter to handle:
- Database results
- External knowledge results
- Combined insights

## **Example Query Processing**

### **Input Query:**
"Find me all suppliers, and then tell me why suppliers in China are different from Suppliers in India in terms of documentation"

### **Multi-Part Detection Result:**
```json
{
  "is_multi_part": true,
  "components": [
    {
      "component_type": "retrieval",
      "intent": "SQL_QUERY",
      "confidence": 0.95,
      "reasoning": "User wants to find suppliers from database",
      "query_text": "Find me all suppliers"
    },
    {
      "component_type": "external_knowledge", 
      "intent": "GENERATE_EXPLANATION",
      "confidence": 0.90,
      "reasoning": "User wants external knowledge about country differences",
      "query_text": "tell me why suppliers in China are different from Suppliers in India in terms of documentation"
    }
  ],
  "primary_intent": "SQL_QUERY",
  "overall_confidence": 0.92
}
```

### **Execution:**
1. **Database Query**: Execute SQL to get all suppliers
2. **External Knowledge Query**: Ask OpenAI about China vs India supplier documentation differences
3. **Response Synthesis**: Combine both results into unified response

### **Final Response Structure:**
```json
{
  "is_multi_part": true,
  "database_results": {
    "suppliers": [...],
    "total_found": 150
  },
  "external_knowledge": {
    "explanation": "Chinese suppliers typically require...",
    "source": "openai_knowledge"
  },
  "synthesized_insights": "Based on your 150 suppliers and industry practices..."
}
```

## **Why This Approach is Optimal**

1. **Minimal Changes**: Leverages existing multi-part infrastructure
2. **Clean Architecture**: Database and external knowledge remain separate concerns
3. **Cost Effective**: Only triggers OpenAI knowledge calls when needed
4. **Scalable**: Easy to add more external knowledge sources later
5. **User Experience**: Provides comprehensive answers combining internal data with external context
6. **No New Intents**: Works within existing intent classification system

## **Benefits**

- **Performance**: Parallel execution of database and knowledge queries
- **Flexibility**: Can handle any combination of database + external knowledge questions
- **Maintainability**: Clear separation of concerns
- **Cost Optimization**: External knowledge calls only when explicitly needed
- **Rich Responses**: Users get both their data AND relevant external context

This approach transforms your system from pure database queries to hybrid queries that can provide comprehensive answers by combining your internal data with OpenAI's general knowledge base.




