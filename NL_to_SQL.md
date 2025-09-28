# Natural Language to SQL System Documentation

## 🎯 **System Overview**

This document provides a comprehensive explanation of how the Supplero application transforms natural language queries into SQL, executes them, and displays the results to users.

## 📁 **Complete End-to-End Flow: Natural Language Query to Data Display**

### **Flow Overview**
```
User Input → Assistant Panel → Frontend API → Backend Processing → SQL Generation → Database Query → Response Formatting → Visual Display
```

---

## 🎨 **1. Frontend Components (User Interface)**

### **1.1 Command Bar & Assistant Root**
**Files:**
- `frontend/app/components/assistant/CommandBar.tsx`
- `frontend/app/components/assistant/AssistantRoot.tsx`

**Key Code Snippets:**

```typescript
// AssistantPanel.tsx - Main query submission
async function handleSubmit(e: React.FormEvent) {
  e.preventDefault();
  setIsLoading(true);
  setError(null);
  setData(null);
  try {
    const res = await fetch("/api/v1/ai-assistant/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, context: pageContext || {} }),
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt || "Request failed");
    }
    const json: ExecuteResponse = await res.json();
    setData(json);
  } catch (err: any) {
    setError(err?.message || "Something went wrong");
  } finally {
    setIsLoading(false);
  }
}
```

### **1.2 Assistant Panel (Main UI)**
**File:** `frontend/app/components/assistant/AssistantPanel.tsx`

**Key Features:**
- Query input form
- Loading states
- Dynamic response rendering
- Multiple data visualization components

**Key Code Snippets:**

```typescript
// Dynamic response rendering based on content structure
function ResponseView({ result, onClose }: { result: Record<string, any>; onClose: () => void }) {
  // Handle multi-part query responses
  if (result?.is_multi_part) {
    return <MultiPartResponseView result={result} onClose={onClose} />;
  }

  // Dynamic response rendering based on content structure
  return <DynamicResponseRenderer result={result} onClose={onClose} />;
}
```

---

## 🌐 **2. Frontend API Routes (Next.js API Layer)**

### **2.1 Execute Route**
**File:** `frontend/app/api/v1/ai-assistant/execute/route.ts`

**Purpose:** Proxies requests to backend AI assistant service

```typescript
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    const backendUrl = buildApiUrl('/api/v1/ai-assistant/execute', true);
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': request.headers.get('Authorization') || '',
        'X-Trace-ID': request.headers.get('X-Trace-ID') || '',
        'X-Correlation-ID': request.headers.get('X-Correlation-ID') || '',
        'X-Span-ID': request.headers.get('X-Span-ID') || '',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(`Backend responded with status: ${response.status}: ${errorData.detail || 'Unknown error'}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to process AI assistant execute', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
```

---

## 🔧 **3. Backend AI Assistant Service**

### **3.1 Main AI Assistant API**
**File:** `backend/app/api/v1/ai_assistant.py`

**Key Components:**
- Intent classification
- Parameter extraction
- SQL generation
- Response formatting

**Key Code Snippets:**

```python
async def process_query(
    self,
    query: str,
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """
    Process a natural language query through the complete AI pipeline.
    """
    start_time = time.time()
    
    try:
        # Step 1.1: Classify intent
        classification_result = await self.intent_classifier.classify_intent(query)
        
        # Step 1.2: Extract parameters
        parameters = await self.parameter_extractor.extract_parameters(
            query, classification_result.intent
        )
        
        # Step 1.3: Execute appropriate handler
        parameters["query"] = query
        execution_result = await self._execute_handler(
            classification_result.intent,
            parameters,
            db,
            current_user
        )
        
        # Step 1.4: Format response
        processing_time_ms = (time.time() - start_time) * 1000
        
        formatted_response = self.response_formatter.format_response(
            intent=classification_result.intent,
            execution_result=execution_result,
            query=query,
            processing_time_ms=processing_time_ms
        )
        
        return formatted_response
        
    except Exception as e:
        # Error handling...
        return error_response
```

### **3.2 Intent Classification**
**File:** `backend/app/api/v1/ai_assistant_utils/intent_classifier.py`

**Purpose:** Classifies natural language queries into specific intents

**Available Intents:**
- `SQL_QUERY` - Standard data retrieval queries
- `SQL_ANALYTICS` - Analytics, reporting, aggregations
- `COMPARISON_QUERY` - Side-by-side comparisons
- `GENERATE_EXPLANATION` - Contextual explanations
- `GENERATE_INSIGHTS` - Strategic insights and recommendations

**Key Code Snippets:**

```python
async def classify_intent(self, query: str) -> IntentClassificationResult:
    """
    Classify the intent of a natural language query using OpenAI.
    """
    try:
        system_prompt = self._build_intent_classification_prompt()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.OPENAI_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Classify this query: {query}"}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 200
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Parse the JSON response
                classification = json.loads(content)
                intent_str = classification.get("intent", "UNKNOWN")
                
                return IntentClassificationResult(
                    intent=IntentType(intent_str),
                    confidence=classification.get("confidence", 0.0),
                    reasoning=classification.get("reasoning", "No reasoning provided"),
                    context_parameters=classification.get("context_parameters")
                )
```

### **3.3 Parameter Extraction**
**File:** `backend/app/api/v1/ai_assistant_utils/parameter_extractor.py`

**Purpose:** Extracts relevant parameters from natural language queries

**Example:**
- **Input:** `"Find suppliers in China with high risk scores above 80"`
- **Output:** `{"country": "China", "min_risk_score": 80, "risk_level": "high"}`

### **3.4 Response Formatting**
**File:** `backend/app/api/v1/ai_assistant_utils/response_formatter.py`

**Purpose:** Formats responses for different intents and data types

---

## 🗄️ **4. SQL Generation & Execution**

### **4.1 SQL Query Generator**
**File:** `backend/app/core/sql_query_generator.py`

**Purpose:** Converts natural language to SQL queries

**Two-Tier Approach:**
1. **Pattern Matching** (Fast, Pre-built queries)
2. **AI SQL Generation** (Flexible, Dynamic queries)

### **4.2 Pattern Matching System**

**What it is:** Pre-built SQL query templates that match common query patterns

**How it works:**
1. System analyzes the natural language query
2. Looks for specific keywords and patterns
3. If a pattern matches, uses a pre-built SQL template
4. If no pattern matches, falls back to AI generation

**Pattern Matching Examples:**

```python
# Example 1: Simple Count Query
# User Query: "How many suppliers do we have?"
if "how many" in query_lower and "supplier" in query_lower:
    sql = "SELECT COUNT(*) as supplier_count FROM suppliers s WHERE s.organization_id = :organization_id AND s.is_active = true"

# Example 2: Risk-based Supplier Query
# User Query: "Show me suppliers with high risk"
elif "supplier" in query_lower and "risk" in query_lower:
    sql = self.query_patterns["suppliers_with_risk_scores"]
```

**Pre-built Templates:**
```sql
-- Suppliers with risk scores
SELECT s.name, s.current_risk_score, s.current_risk_level, s.geopolitical_risk, s.financial_risk, s.operational_risk, s.compliance_risk, s.esg_risk
FROM suppliers s
WHERE s.organization_id = :organization_id
ORDER BY s.current_risk_score DESC

-- Expiring contracts
SELECT c.title, c.expires_at, c.contract_value, c.currency, cp.name as supplier_name
FROM contracts c
LEFT JOIN contract_parties cp ON c.id = cp.contract_id AND cp.role = 'supplier'
WHERE c.organization_id = :organization_id 
AND c.expires_at BETWEEN NOW() AND NOW() + INTERVAL '30 days'
ORDER BY c.expires_at ASC
```

### **4.3 AI SQL Generation**

**When it's used:** Only when pattern matching fails

**Key Code Snippets:**

```python
async def generate_sql_query(
    self,
    natural_language_query: str,
    intent_type: str,
    parameters: Dict[str, Any],
    organization_id: int
) -> SQLQueryResult:
    """
    Generate SQL query from natural language input.
    """
    try:
        # First, try to match against common patterns
        pattern_result = self._try_pattern_matching(natural_language_query, intent_type, parameters, organization_id)
        if pattern_result:
            return pattern_result
        
        # If no pattern matches, use AI to generate SQL
        return await self._generate_sql_with_ai(natural_language_query, intent_type, parameters, organization_id)
        
    except Exception as e:
        logger.error("Failed to generate SQL query", error=str(e))
        return self._create_fallback_query(intent_type, parameters, organization_id)
```

### **4.4 SQL Execution Handlers**
**File:** `backend/app/api/v1/handlers/simplified_sql_handlers.py`

**Purpose:** Executes different types of SQL queries

**Key Code Snippets:**

```python
async def execute_sql_query(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute generic SQL query - the main handler for most queries"""
    start_time = time.time()
    try:
        original_query = parameters.get("query") or parameters.get("raw_query")
        
        # Generate SQL query
        sql_result = await sql_query_generator.generate_sql_query(
            natural_language_query=original_query,
            intent_type=IntentType.SQL_QUERY.value,
            parameters=parameters,
            organization_id=current_user.organization_id
        )
        
        # Execute the generated SQL query
        result = db.execute(text(sql_result.query), sql_result.parameters)
        rows = result.fetchall()
        
        # Convert rows to dictionaries
        results = []
        for row in rows:
            result_dict = dict(row._mapping)
            results.append(result_dict)
        
        return BaseHandler.create_success_response(
            message=f"Found {len(results)} results using SQL",
            parameters=parameters,
            data={
                "results": results,
                "total_found": len(results),
                "search_strategy": "sql_query",
                "search_method": "generated_sql",
                "sql_query": sql_result.query,
                "query_confidence": sql_result.confidence,
                "query_complexity": sql_result.estimated_complexity,
                "search_performance": {
                    "total_time_ms": (time.time() - start_time) * 1000,
                    "phase": "sql_query"
                }
            }
        )
```

---

## 🔄 **5. Complete Data Flow**

### **Step-by-Step Process:**

1. **User Input** → User types query in Assistant Panel
2. **Frontend API** → Request sent to `/api/v1/ai-assistant/execute`
3. **Backend Processing** → AI Assistant service processes query
4. **Intent Classification** → Determines query type (SQL_QUERY, SQL_ANALYTICS, etc.)
5. **Parameter Extraction** → Extracts relevant parameters from query
6. **SQL Generation** → Converts natural language to SQL using pattern matching or AI
7. **Database Execution** → Executes SQL query against PostgreSQL
8. **Response Formatting** → Formats results for frontend display
9. **Visual Display** → Results rendered in Assistant Panel with appropriate components

### **Key Data Transformations:**

```
Natural Language Query
    ↓
Intent Classification (SQL_QUERY, SQL_ANALYTICS, etc.)
    ↓
Parameter Extraction (filters, criteria, etc.)
    ↓
SQL Query Generation (using pattern matching or AI)
    ↓
Database Query Execution (PostgreSQL)
    ↓
Result Formatting (JSON response)
    ↓
Frontend Component Rendering (cards, tables, charts)
```

---

## 🤖 **6. OpenAI API Calls Analysis**

### **Total OpenAI Calls Per Query:**

#### **Standard Single Query Flow:**
1. **Intent Classification** - 1 call
2. **Parameter Extraction** - 1 call  
3. **SQL Generation** - 1 call (only if pattern matching fails)

**Total: 2-3 calls per query**

#### **Complex Query Flow:**
1. **Intent Classification** - 1 call
2. **Parameter Extraction** - 1 call
3. **Multi-Part Detection** - 1 call (optional)
4. **SQL Generation** - 1 call (only if pattern matching fails)

**Total: 3-4 calls per query**

### **OpenAI API Call Details:**

#### **1. Intent Classification**
- **File:** `backend/app/api/v1/ai_assistant_utils/intent_classifier.py`
- **Model:** Default OpenAI model
- **Purpose:** Determine query intent
- **Always Called:** Yes

#### **2. Parameter Extraction**
- **File:** `backend/app/api/v1/ai_assistant_utils/parameter_extractor.py`
- **Model:** Default OpenAI model
- **Purpose:** Extract structured parameters
- **Always Called:** Yes

#### **3. SQL Generation**
- **File:** `backend/app/core/sql_query_generator.py`
- **Model:** GPT-4 (more powerful)
- **Purpose:** Generate SQL queries
- **Conditional:** Only when pattern matching fails

#### **4. Multi-Part Detection** (Optional)
- **File:** `backend/app/api/v1/ai_assistant_utils/intent_classifier.py`
- **Model:** Default OpenAI model
- **Purpose:** Detect complex multi-part queries
- **Conditional:** Only for complex queries

---

## 🎯 **7. Parameter Extraction vs SQL Generation**

### **Parameter Extraction**
- **Purpose:** Extract structured data from natural language
- **Input:** Natural language query
- **Output:** Key-value pairs of parameters
- **When:** Always happens (Step 2)
- **Example:**
  - **Input:** `"Find suppliers in China with high risk scores above 80"`
  - **Output:** `{"country": "China", "min_risk_score": 80, "risk_level": "high"}`

### **SQL Generation**
- **Purpose:** Convert natural language + parameters into executable SQL
- **Input:** Natural language query + extracted parameters
- **Output:** Complete SQL query
- **When:** Only when pattern matching fails (Step 3)
- **Example:**
  - **Input:** Natural language + parameters
  - **Output:** 
  ```sql
  SELECT s.name, s.current_risk_score, s.current_risk_level, s.industry, s.country
  FROM suppliers s
  WHERE s.organization_id = :organization_id 
  AND s.country = :country
  AND s.current_risk_score > :min_risk_score
  ORDER BY s.current_risk_score DESC
  LIMIT 20
  ```

---

## 🏗️ **8. Design Principles for Multiple OpenAI Calls**

### **Why Separate Calls Instead of Single Call:**

#### **1. Single Responsibility Principle (SRP)**
Each component has one clear job:
- **Intent Classifier**: "What does the user want to do?"
- **Parameter Extractor**: "What specific data do I need?"
- **SQL Generator**: "How do I query the database?"

#### **2. Modularity & Maintainability**
- **Independent Updates**: You can improve parameter extraction without touching SQL generation
- **Easier Debugging**: If SQL generation fails, you know exactly which step has the issue
- **Testing**: Each component can be unit tested independently
- **Code Reuse**: Parameter extraction can be used for other purposes beyond SQL

#### **3. Cost Optimization**
- **Right Tool for the Job**: Intent classification and parameter extraction are simpler tasks that can use cheaper models
- **Conditional Execution**: SQL generation only happens when pattern matching fails
- **Token Efficiency**: Smaller, focused prompts are more efficient than one massive prompt
- **Fallback Strategies**: If one step fails, others can still work

#### **4. Performance & Scalability**
- **Parallel Processing**: These could potentially be run in parallel
- **Caching**: Intent classification results could be cached for similar queries
- **Load Distribution**: Different components can be scaled independently
- **Faster Response**: Smaller, focused API calls are typically faster

#### **5. Error Handling & Resilience**
- **Granular Error Recovery**: If parameter extraction fails, you can still try SQL generation with defaults
- **Partial Success**: System can work even if one component fails
- **Better Error Messages**: Users get specific feedback about which step failed
- **Fallback Mechanisms**: Each step can have its own fallback strategy

#### **6. Flexibility & Extensibility**
- **Different Models**: Intent classification might use GPT-3.5, SQL generation uses GPT-4
- **Custom Logic**: Each step can have custom business logic before/after AI calls
- **A/B Testing**: You can test different approaches for each component independently
- **Feature Flags**: Enable/disable specific components without affecting others

---

## 🎨 **9. Frontend Display Components**

The Assistant Panel includes multiple specialized components for different data types:

- **SuppliersCard** - Displays supplier information
- **ContractsCard** - Shows contract details
- **AnalyticsResultsCard** - Renders analytical data
- **RiskDistributionCard** - Visualizes risk metrics
- **CitationsCard** - Shows document citations
- **GenericDataCard** - Fallback for any structured data

---

## 🔧 **10. Configuration & Utilities**

### **10.1 API Configuration**
**File:** `frontend/app/lib/api-config.ts`

**Purpose:** Manages API URLs for different environments

### **10.2 Database Schema**
**File:** `backend/app/core/sql_query_generator.py` (schema context)

**Purpose:** Provides database schema information for AI SQL generation

---

## 💡 **11. Key Benefits of This Architecture**

### **Performance Benefits:**
- **Pattern Matching**: Common queries are instant (no API calls)
- **Conditional AI Usage**: Only complex queries use expensive AI
- **Optimized Queries**: Pre-built queries are performance-optimized

### **Cost Benefits:**
- **Minimal OpenAI Usage**: Only 2-3 calls per query on average
- **Right Model for Task**: Cheaper models for simple tasks, GPT-4 only for complex SQL
- **Pattern Matching**: Free execution for common queries

### **Reliability Benefits:**
- **Tested Queries**: Pre-built queries are guaranteed to work
- **Fallback Mechanisms**: Multiple layers of fallback
- **Error Recovery**: Granular error handling at each step

### **Maintainability Benefits:**
- **Modular Design**: Each component can be updated independently
- **Clear Separation**: Easy to understand and debug
- **Extensible**: Easy to add new patterns or intents

---

## 🎯 **12. Summary**

This Natural Language to SQL system demonstrates a well-architected approach that:

1. **Maximizes Performance** through pattern matching for common queries
2. **Minimizes Costs** through intelligent AI usage
3. **Ensures Reliability** through multiple fallback mechanisms
4. **Maintains Flexibility** through modular, extensible design
5. **Provides Great UX** through fast responses and rich visualizations

The system successfully transforms natural language queries into SQL, executes them against the database, and presents the results in a user-friendly visual format through a robust, scalable architecture.
