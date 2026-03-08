# Quick Start - Priority Refactorings - OptiCode Python Refactoring Platform

## 🚀 Get Started in 3 Minutes

### Step 1: Install Dependencies (1 minute)

```bash
cd IT22606860-code-refactor-python
pip install -r requirements.txt
```

Wait for all packages to install. You'll see packages like Flask, bandit, radon, astor being installed.

---

### Step 2: Start the Services (30 seconds)

Open **3 separate terminals** and run:

**Terminal 1 - Main Refactoring API:**
```bash
python refactor_api.py
```
You should see: `[SERVER] Running on: http://localhost:8000`

**Terminal 2 - Risk Analysis API:**
```bash
python risk_analysis_api.py
```
You should see: `[SERVER] Running on: http://localhost:8001`

**Terminal 3 - Learning API:**
```bash
python learning_api.py
```
You should see: `[SERVER] Running on: http://localhost:8002`

---

### Step 3: Test with Sample Requests (1 minute)

#### Test 1: Refactor Simple Code

Create a file `test_refactor.py`:

```python
import requests
import json

code = """
def check_positive(number):
    if number > 0:
        return True
    else:
        return False
"""

response = requests.post('http://localhost:8000/api/refactor', 
    json={
        'code': code,
        'language': 'python',
        'use_ast': True
    }
)

result = response.json()
print("Original Code:")
print(result['original_code'])
print("\nRefactored Code:")
print(result['refactored_code'])
print("\nChanges Made:")
for change in result['changes']:
    print(f"  - {change['description']}")
```

Run it:
```bash
python test_refactor.py
```

**Expected Output:**
```
Original Code:
def check_positive(number):
    if number > 0:
        return True
    else:
        return False

Refactored Code:
def check_positive(number):
    return number > 0

Changes Made:
  - Simplified conditional expressions
```

---

#### Test 2: Analyze Code Quality

Create `test_analyze.py`:

```python
import requests

code = """
def process_data(data):
    result = []
    for i in range(len(data)):
        item = data[i]
        if item > 0:
            result.append(item * 2)
    return result
"""

response = requests.post('http://localhost:8000/api/analyze',
    json={'code': code}
)

result = response.json()
print(f"Overall Score: {result['overall_score']['score']}/100")
print(f"Grade: {result['overall_score']['grade']}")
print(f"Complexity: {result['complexity']['average_complexity']}")
print(f"Lines of Code: {result['metrics']['loc']}")
```

---

#### Test 3: Get Learning Content

```bash
# In your browser or using curl
curl http://localhost:8002/api/categories
curl http://localhost:8002/api/random-tip
```

---

## 📋 Common Use Cases

### Use Case 1: Student Learning Refactoring

1. Write some messy code
2. Submit to `/api/refactor` with `use_ast: true`
3. Get refactored code + explanations
4. Compare before/after
5. Learn from the changes!

### Use Case 2: Check Code Before Submission

1. Submit your code to `/api/analyze`
2. Get quality score, complexity, and issues
3. Fix issues reported
4. Check best practices with `/api/best-practices`
5. Ensure high quality before submission

### Use Case 3: Learn Best Practices

1. Browse learning content via `/api/categories`
2. Read specific topics via `/api/topic/<category>/<topic>`
3. Get daily tips from `/api/random-tip`
4. Apply learnings to your code

---

## 🎯 Quick Reference

### Port Numbers
- **8000**: Main Refactoring API (AST + Analysis)
- **8001**: Risk Analysis API
- **8002**: Learning/Educational API

### Key Endpoints

#### Refactoring API (Port 8000)
```
POST /api/refactor           → Refactor code (AST)
POST /api/analyze            → Full code analysis
POST /api/best-practices     → Best practices check
POST /api/ethical-analysis   → Ethical coding check
POST /api/suggest-refactorings → Get suggestions
POST /api/code-structure     → Structure analysis
GET  /health                 → Check server status
```

#### Risk Analysis API (Port 8001)
```
POST /api/risk-analyze       → Risk assessment
GET  /health                 → Check server status
```

#### Learning API (Port 8002)
```
GET /api/categories          → List all topics
GET /api/category/<name>     → Get category
GET /api/topic/<cat>/<topic> → Get topic details
GET /api/search?q=<query>    → Search content
GET /api/random-tip          → Random tip
GET /health                  → Check server status
```

---

## 💡 Pro Tips

1. **Always check `/health`** endpoints first to verify servers are running
2. **Use `use_ast: true`** in refactor requests for AST-based refactoring
3. **Enable `get_suggestions: true`** to get AI-powered explanations
4. **Start with `/api/analyze`** to understand your code quality first
5. **Browse learning content** to understand the "why" behind refactorings

---

## 🐛 Troubleshooting

### Problem: "Connection refused"
**Solution:** Make sure the server is running on that port

### Problem: "Module not found"
**Solution:** Run `pip install -r requirements.txt` again

### Problem: "Port already in use"
**Solution:** 
- Kill the process using that port
- Or change port in the respective `.py` file

### Problem: "AST analysis failed"
**Solution:** Check if your Python code has syntax errors

---

## 📚 Next Steps

1. ✅ Read the full [README.md](README.md) for detailed documentation
2. ✅ Explore each module's code to understand implementation
3. ✅ Try the learning API to learn about each concept
4. ✅ Build a frontend to interact with these APIs
5. ✅ Experiment with different code samples

---

## 🎓 Learning Path

**Day 1:** Basic refactoring  
→ Use `/api/refactor` with simple examples

**Day 2:** Code analysis  
→ Use `/api/analyze` and understand metrics

**Day 3:** Best practices  
→ Use `/api/best-practices` and learn SOLID, DRY, etc.

**Day 4:** Security & Ethics  
→ Use `/api/ethical-analysis` and learn responsible coding

**Day 5:** Risk assessment  
→ Use `/api/risk-analyze` before applying refactorings

---

**You're all set! Happy coding! 🚀**
