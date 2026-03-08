# OptiCode - Python Code Refactoring & Learning Platform

## 🎯 Project Overview

**OptiCode** is a comprehensive educational platform designed to help developers learn and master Python code refactoring, best practices, ethical coding, and code analysis techniques. This project uses **AST (Abstract Syntax Tree)** for intelligent code refactoring and **LLM (Large Language Models)** for suggestions, explanations, and risk analysis.

**Student ID:** IT22606860

---

## 🚀 Features

### 1. **AST-Based Code Refactoring**
- **Simplify Conditionals**: Automatically simplify complex boolean expressions
- **Extract Complex Expressions**: Break down complex expressions into readable variables
- **Improve Loops**: Optimize loop constructs (e.g., convert `range(len())` to `enumerate()`)
- **Refactor Magic Numbers**: Identify and suggest named constants for magic numbers
- **Code Structure Analysis**: Analyze functions, classes, imports, and complexity

### 2. **Comprehensive Code Analysis**
- **Complexity Metrics**: Cyclomatic complexity using Radon
- **Maintainability Index**: Calculate code maintainability score
- **Security Scanning**: Identify security vulnerabilities using Bandit
- **Style Checking**: PEP 8 compliance and style issues
- **Code Smells Detection**: Long methods, large classes, duplicate code, etc.
- **Overall Quality Score**: Comprehensive scoring system

### 3. **Best Practices Checking**
- **SOLID Principles**: Single Responsibility, Open/Closed, Liskov Substitution, etc.
- **DRY Principle**: Don't Repeat Yourself - detect code duplication
- **Documentation Quality**: Check docstrings and comments
- **Error Handling**: Validate exception handling practices
- **Pythonic Patterns**: List comprehensions, context managers, f-strings, etc.
- **Performance Checks**: Identify performance anti-patterns

### 4. **Ethical Coding Analysis**
- **Inclusive Language**: Detect non-inclusive terms (master/slave, whitelist/blacklist, etc.)
- **Data Privacy**: Check for hardcoded credentials, PII handling
- **Accessibility**: Ensure code considers accessibility requirements
- **Security Ethics**: Validate secure coding practices
- **Environmental Impact**: Check resource efficiency

### 5. **Risk Analysis**
- **AI-Powered Risk Assessment**: Using DeepSeek LLM
- **Technical Risk Metrics**: Compare original vs refactored code
- **Risk Scoring**: 0-100 scale with severity levels
- **Detailed Recommendations**: Actionable suggestions for risk mitigation

### 6. **Educational Content API**
- **Learning Modules**: Refactoring, best practices, code analysis, security, ethics
- **Interactive Examples**: Before/after code examples
- **Searchable Content**: Search through educational materials
- **Random Tips**: Daily coding tips for continuous learning

---

## 📂 Project Structure

```
IT22606860-code-refactor-python/
├── refactor_api.py              # Main API - AST refactoring & LLM suggestions
├── risk_analysis_api.py         # Risk analysis API
├── learning_api.py              # Educational content API
├── ast_refactor.py              # AST-based refactoring engine
├── code_analyzer.py             # Code quality analyzer
├── best_practices.py            # Best practices checker
├── ethical_code_analyzer.py     # Ethical coding analyzer
├── requirements.txt             # Python dependencies
├── README.md                    # This file
└── model/                       # Legacy: Trained model (deprecated)
    └── final-code-refactor-model/
```

---

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Install Dependencies

```bash
cd IT22606860-code-refactor-python
pip install -r requirements.txt
```

### Step 2: Set Up Environment Variables (Optional)

Create a `.env` file if you want to customize the API:

```env
# DeepSeek API Configuration (for LLM features)
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://openrouter.ai/api/v1
DEEPSEEK_MODEL=deepseek/deepseek-r1-0528:free
```

---

## 🚀 Running the Services

This project consists of **3 independent APIs** running on different ports:

### 1. Main Refactoring API (Port 8000)

```bash
python refactor_api.py
```

**Features:**
- AST-based code refactoring
- Code analysis
- Best practices checking
- Ethical analysis
- Code structure analysis
- Code execution

**Endpoints:**
- `POST /api/refactor` - Refactor Python code
- `POST /api/analyze` - Comprehensive code analysis
- `POST /api/best-practices` - Check best practices
- `POST /api/ethical-analysis` - Ethical coding analysis
- `POST /api/suggest-refactorings` - Get refactoring suggestions
- `POST /api/code-structure` - Analyze code structure
- `POST /api/execute` - Execute Python code safely
- `GET /health` - Health check

### 2. Risk Analysis API (Port 8001)

```bash
python risk_analysis_api.py
```

**Features:**
- AI-powered risk assessment
- Technical analysis using AST
- Risk scoring and visualization
- Detailed recommendations

**Endpoints:**
- `POST /api/risk-analyze` - Analyze refactoring risks
- `GET /health` - Health check

### 3. Learning API (Port 8002)

```bash
python learning_api.py
```

**Features:**
- Educational content about refactoring
- Best practices tutorials
- Security guidelines
- Ethical coding practices
- Interactive examples

**Endpoints:**
- `GET /api/categories` - List all learning categories
- `GET /api/category/<name>` - Get category details
- `GET /api/topic/<category>/<topic>` - Get topic details
- `GET /api/search?q=<query>` - Search content
- `GET /api/random-tip` - Get random coding tip
- `GET /health` - Health check

---

## 📡 API Usage Examples

### 1. Refactor Code (AST-Based)

```bash
curl -X POST http://localhost:8000/api/refactor \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def calc(x):\n    if x > 0:\n        return True\n    else:\n        return False",
    "language": "python",
    "use_ast": true,
    "get_suggestions": true
  }'
```

**Response:**
```json
{
  "success": true,
  "refactored_code": "def calc(x):\n    return x > 0",
  "original_code": "...",
  "method": "AST-based refactoring",
  "changes": [
    {
      "type": "simplify_conditionals",
      "description": "Simplified conditional expressions"
    }
  ],
  "ai_suggestions": {
    "success": true,
    "suggestions": "..."
  },
  "processing_time": 245.67
}
```

### 2. Analyze Code Quality

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def process_data(data):\n    result = []\n    for item in data:\n        result.append(item * 2)\n    return result"
  }'
```

**Response:**
```json
{
  "success": true,
  "metrics": {
    "loc": 5,
    "lloc": 4,
    "comments": 0
  },
  "complexity": {
    "average_complexity": 2,
    "functions": [...]
  },
  "security": {
    "total_issues": 0
  },
  "overall_score": {
    "score": 85,
    "grade": "B",
    "quality": "Good"
  }
}
```

### 3. Check Best Practices

```bash
curl -X POST http://localhost:8000/api/best-practices \
  -H "Content-Type: application/json" \
  -d '{
    "code": "class UserManager:\n    def create_user(self): pass\n    def delete_user(self): pass\n    def send_email(self): pass"
  }'
```

### 4. Analyze Refactoring Risk

```bash
curl -X POST http://localhost:8001/api/risk-analyze \
  -H "Content-Type: application/json" \
  -d '{
    "original_code": "def old_function():\n    x = 5\n    return x * 2",
    "refactored_code": "def new_function():\n    MULTIPLIER = 2\n    x = 5\n    return x * MULTIPLIER",
    "language": "python"
  }'
```

### 5. Get Learning Content

```bash
# List categories
curl http://localhost:8002/api/categories

# Get specific topic
curl http://localhost:8002/api/topic/refactoring/extract_method

# Search content
curl http://localhost:8002/api/search?q=SOLID

# Get random tip
curl http://localhost:8002/api/random-tip
```

---

## 🎓 Educational Use Cases

### For Students Learning Refactoring:
1. **Submit messy code** → Get AST-based refactored version
2. **Compare before/after** → Understand what changed and why
3. **Read AI explanations** → Learn the reasoning behind changes
4. **Check best practices** → Identify violations and learn corrections
5. **Explore learning content** → Access tutorials and examples

### For Educators:
1. **Demonstrate refactoring** → Show real examples with AST
2. **Teach code quality** → Use metrics to explain good code
3. **Explain security** → Show actual vulnerabilities with Bandit
4. **Discuss ethics** → Highlight inclusive language and privacy
5. **Assess student code** → Use comprehensive analysis for grading

---

## 🔑 Key Technologies

### AST Analysis
- **astor**: AST to source code conversion
- **Python ast module**: Code parsing and transformation

### Code Quality Tools
- **Radon**: Complexity and maintainability metrics
- **Bandit**: Security vulnerability scanning
- **Pylint**: Code quality checking
- **Black**: Code formatting
- **Flake8**: Style enforcement

### AI/ML
- **DeepSeek R1**: LLM for suggestions and explanations
- **OpenRouter**: API gateway for LLM access
- **Transformers**: (Legacy) Local model support

### Web Framework
- **Flask**: REST API server
- **Flask-CORS**: Cross-origin support for frontend

---

## 🎯 Design Philosophy

### 1. **Education First**
- Clear explanations for every analysis
- Examples showing before/after
- Learning content integrated with tools

### 2. **AST Over ML**
- Deterministic refactoring using AST
- Faster and more reliable
- No dependency on external models
- ML used only for suggestions and explanations

### 3. **Comprehensive Analysis**
- Quality, security, ethics, best practices
- Multiple dimensions of code health
- Actionable recommendations

### 4. **Modern Python**
- PEP 8 compliance
- Type hints support
- Python 3.8+ features

---

## 🔄 Migration from LLM to AST

**Why AST?**
- ✅ **Deterministic**: Same input = same output
- ✅ **Fast**: No network latency
- ✅ **Reliable**: No model failures
- ✅ **Transparent**: Clear transformation rules
- ✅ **Educational**: Can explain each transformation

**What about LLM?**
- Still used for **suggestions** and **explanations**
- Risk analysis leverages LLM understanding
- Best for **human-facing content**, not code transformation

---

## 🐛 Troubleshooting

### Issue: Import errors when running APIs

**Solution:**
```bash
# Make sure you're in the correct directory
cd IT22606860-code-refactor-python

# Install all dependencies
pip install -r requirements.txt
```

### Issue: Port already in use

**Solution:**
```bash
# Change port in the respective file
# refactor_api.py: line ~700 - change port=8000
# risk_analysis_api.py: line ~400 - change port=8001
# learning_api.py: line ~600 - change port=8002
```

### Issue: DeepSeek API errors

**Solution:**
- Check your API key in the code
- Verify internet connection
- API rate limits may apply (free tier)

---

## 📊 Frontend Integration

### CORS Enabled
All APIs have CORS enabled for easy frontend integration.

### Example React Fetch:

```javascript
// Refactor code
const response = await fetch('http://localhost:8000/api/refactor', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    code: sourceCode,
    language: 'python',
    use_ast: true,
    get_suggestions: true
  })
});

const result = await response.json();
console.log(result.refactored_code);
```

---

## 📈 Future Enhancements

- [ ] Support for more languages (JavaScript, Java)
- [ ] Web-based UI for easier interaction
- [ ] Code diff visualization
- [ ] Integration with VS Code extension
- [ ] Export reports as PDF
- [ ] Batch processing for multiple files
- [ ] Custom refactoring rules
- [ ] Team collaboration features

---

## 🤝 Contributing

This is an educational project. Suggestions and improvements are welcome!

---

## 📄 License

This project is created for educational purposes as part of academic work.

---

## 👤 Author

**Student ID:** IT22606860  
**Project:** Python Code Refactoring & Learning Platform  
**Focus:** AST-based refactoring, code quality analysis, ethical coding practices

---

## 📞 Support

For issues or questions about this project, please check:
1. This README file
2. Code comments in each module
3. API `/health` endpoints for status

---

**Happy Coding! 🎉**
