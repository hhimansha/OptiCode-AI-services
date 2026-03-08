# LLM Chat Assistant API

**Port:** 8001  
**Purpose:** AI-powered chatbot for refactoring assistance and code analysis

---

## Quick Start

### 1. Install Dependencies

```bash
pip install Flask flask-cors openai
```

### 2. Set Environment Variables

**Option A: Using OpenRouter (Recommended)**
```bash
export OPENROUTER_API_KEY="your-openrouter-api-key-here"
```

**Option B: Using OpenAI**
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
export OPENAI_BASE_URL="https://api.openai.com/v1"
export LLM_MODEL="gpt-4-turbo-preview"
```

### 3. Start the Server

```bash
cd IT22606860-code-refactor-python
python llm_chat_api.py
```

You should see:
```
================================================================================
 🤖 LLM CHAT ASSISTANT API
================================================================================
 📍 Port: 8001
 🧠 Model: deepseek/deepseek-chat
 ✅ LLM Available: True
================================================================================

 🎯 AVAILABLE ENDPOINTS:
================================================================================
  POST   /chat                    - AI chat assistant
  GET    /chat/history            - Get chat history
  DELETE /chat/history            - Clear chat history
  POST   /analyze/comparison      - Advanced code comparison
  POST   /insights                - Get refactoring insights
  GET    /health                  - Health check
================================================================================

 🚀 Starting server on http://localhost:8001
```

---

## API Endpoints

### 1. Chat with AI Assistant

**Endpoint:** `POST /chat`

**Request:**
```json
{
  "message": "How can I optimize this Python code for better performance?",
  "history": [
    {"role": "user", "content": "Previous message"},
    {"role": "assistant", "content": "Previous response"}
  ]
}
```

**Response:**
```json
{
  "response": "Here are several ways to optimize your Python code...",
  "metadata": {
    "analysisType": "performance",
    "tokensUsed": 150,
    "timestamp": "2026-02-09T10:00:00Z",
    "model": "deepseek/deepseek-chat"
  }
}
```

**Example Questions:**
- "How did you refactor this code?"
- "What are the risks in this code?"
- "How can I improve my refactoring skills?"
- "What patterns should I use to increase performance?"
- "Explain guard clauses with an example"

---

### 2. Advanced Code Comparison

**Endpoint:** `POST /analyze/comparison`

**Request:**
```json
{
  "before": "result = []\nfor i in range(len(items)):\n    if items[i] > 0:\n        result.append(items[i] * 2)",
  "after": "result = [item * 2 for item in items if item > 0]",
  "language": "python"
}
```

**Response:**
```json
{
  "analysis": {
    "memoryOptimization": {
      "before": {
        "estimatedMemory": "~2.4 KB",
        "complexityScore": 65,
        "issues": [
          "Manual loop creates temporary variables",
          "Multiple memory allocations"
        ]
      },
      "after": {
        "estimatedMemory": "~1.2 KB",
        "complexityScore": 95,
        "improvements": [
          "Single expression with no intermediate variables",
          "Optimized list comprehension"
        ]
      },
      "improvement": "50%"
    },
    "performance": {
      "before": {
        "timeComplexity": "O(n)",
        "spaceComplexity": "O(n)",
        "bottlenecks": ["Manual index management", "Range iteration overhead"]
      },
      "after": {
        "timeComplexity": "O(n)",
        "spaceComplexity": "O(n)",
        "optimizations": ["Built-in comprehension optimization", "Direct iteration"]
      },
      "improvement": "~30% faster"
    },
    "codeQuality": {
      "before": {
        "linesOfCode": 4,
        "maintainabilityIndex": 70,
        "cyclomaticComplexity": 2
      },
      "after": {
        "linesOfCode": 1,
        "maintainabilityIndex": 98,
        "cyclomaticComplexity": 1
      }
    },
    "refactoringPatterns": [
      "List Comprehension",
      "Pythonic Iteration",
      "Single Expression"
    ],
    "risks": {
      "resolved": [
        "Off-by-one errors eliminated",
        "Index management issues removed"
      ],
      "remaining": [
        "Ensure items list is not None"
      ]
    }
  },
  "metadata": {
    "language": "python",
    "beforeLines": 4,
    "afterLines": 1,
    "timestamp": "2026-02-09T10:00:00Z"
  }
}
```

---

### 3. Get Refactoring Insights

**Endpoint:** `POST /insights`

**Request:**
```json
{
  "code": "def process_data(items):\n    result = []\n    for i in range(len(items)):\n        if items[i] > 0:\n            result.append(items[i])\n    return result",
  "focus": "performance"
}
```

**Focus Options:**
- `"memory"` - Memory optimization insights
- `"performance"` - Performance optimization insights
- `"quality"` - Code quality improvements
- `"general"` - Comprehensive analysis (default)

**Response:**
```json
{
  "insights": {
    "analysis": "Detailed analysis text with recommendations...",
    "focus": "performance",
    "codeLength": 120,
    "linesOfCode": 6
  },
  "metadata": {
    "focus": "performance",
    "timestamp": "2026-02-09T10:00:00Z",
    "model": "deepseek/deepseek-chat"
  }
}
```

---

### 4. Get Chat History

**Endpoint:** `GET /chat/history`

**Response:**
```json
{
  "history": [
    {
      "id": 1,
      "role": "user",
      "content": "How can I optimize this code?",
      "timestamp": "2026-02-09T10:00:00Z"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "Here are some optimization strategies...",
      "timestamp": "2026-02-09T10:00:05Z"
    }
  ],
  "count": 2
}
```

---

### 5. Clear Chat History

**Endpoint:** `DELETE /chat/history`

**Response:**
```json
{
  "success": true,
  "message": "Chat history cleared (2 messages)",
  "clearedCount": 2
}
```

---

### 6. Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "service": "LLM Chat Assistant",
  "model": "deepseek/deepseek-chat",
  "version": "1.0.0",
  "port": 8001,
  "uptime": 3600,
  "llmAvailable": true,
  "features": [
    "AI Chat Assistant",
    "Code Comparison Analysis",
    "Refactoring Insights",
    "Memory Optimization Analysis",
    "Performance Analysis"
  ],
  "chatHistory": {
    "messages": 10,
    "stored": true
  }
}
```

---

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LLM_PORT` | Server port | 8001 | No |
| `OPENROUTER_API_KEY` | OpenRouter API key | - | Yes* |
| `OPENAI_API_KEY` | OpenAI API key | - | Yes* |
| `OPENAI_BASE_URL` | API base URL | https://openrouter.ai/api/v1 | No |
| `LLM_MODEL` | Model name | deepseek/deepseek-chat | No |
| `MAX_TOKENS` | Max response tokens | 2000 | No |
| `TEMPERATURE` | Sampling temperature | 0.7 | No |

*Either OPENROUTER_API_KEY or OPENAI_API_KEY is required

---

## Testing with curl

### Test Chat
```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the best practices for Python refactoring?"
  }'
```

### Test Code Comparison
```bash
curl -X POST http://localhost:8001/analyze/comparison \
  -H "Content-Type: application/json" \
  -d '{
    "before": "x = []\nfor i in data:\n    x.append(i*2)",
    "after": "x = [i*2 for i in data]",
    "language": "python"
  }'
```

### Test Health
```bash
curl http://localhost:8001/health
```

---

## Integration with Frontend

Your frontend (running on port 5173) should call these endpoints:

```javascript
// In your frontend API service
const LLM_API_URL = 'http://localhost:8001';

// Chat with AI
const response = await fetch(`${LLM_API_URL}/chat`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: userMessage,
    history: chatHistory
  })
});

// Analyze code comparison
const analysis = await fetch(`${LLM_API_URL}/analyze/comparison`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    before: originalCode,
    after: refactoredCode,
    language: 'python'
  })
});
```

---

## Features

### ✅ AI Chat Assistant
- Answers refactoring questions
- Explains patterns and best practices
- Provides code examples
- Remembers conversation context

### ✅ Advanced Code Comparison
- Memory optimization analysis (before/after)
- Performance metrics (time/space complexity)
- Code quality scores
- Refactoring patterns identification
- Risk assessment

### ✅ Refactoring Insights
- Actionable recommendations
- Pattern suggestions
- Complexity analysis
- Focus areas: memory, performance, quality

### ✅ Chat History
- Stores conversation history
- Retrieves past conversations
- Clear history on demand

---

## Troubleshooting

### "LLM service is not available"
**Solution:** Set your API key
```bash
export OPENROUTER_API_KEY="your-key-here"
```

### "Connection refused"
**Solution:** Make sure the server is running on port 8001
```bash
python llm_chat_api.py
```

### "Port already in use"
**Solution:** Change the port
```bash
export LLM_PORT=8002
python llm_chat_api.py
```

---

## Production Considerations

1. **Database Storage:** Replace in-memory chat history with database (MongoDB, PostgreSQL)
2. **Authentication:** Add API key authentication for frontend requests
3. **Rate Limiting:** Implement rate limiting to prevent abuse
4. **Caching:** Cache common responses to reduce API costs
5. **Monitoring:** Add logging and monitoring for API calls
6. **Error Handling:** Enhance error messages and retry logic

---

## Example Chat Conversations

**User:** "What are the risks in using nested loops?"

**Assistant:** "Nested loops can have several risks:

1. **Performance Risk:** Time complexity increases multiplicatively (O(n²), O(n³), etc.)
2. **Memory Risk:** If creating intermediate data structures in inner loops
3. **Maintainability Risk:** Hard to understand and debug
4. **Off-by-one Risk:** More chances for index errors

Example of risky nested loop:
```python
for i in range(len(items)):
    for j in range(len(items)):
        # O(n²) complexity
```

Better alternatives:
- Use list comprehensions
- Use built-in functions (map, filter)
- Consider algorithm optimization..."

---

**Ready to use!** Start the server and integrate with your frontend chatbot. 🚀
