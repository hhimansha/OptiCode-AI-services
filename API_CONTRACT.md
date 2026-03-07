# OptiCode AI Services — API Contract

Base URL: `http://localhost:8000` (dev) | `http://<server>:8000` (prod)

CORS: All origins allowed (`*`).

---

## Existing Endpoints (unchanged)

### `POST /api/IT22601360/extract`
Extract concepts from a **single raw code string**.

**Request:**
```json
{
  "code": "def binary_search(arr, target): ...",
  "language": "python"
}
```

**Response:**
```json
{
  "success": true,
  "concepts": [
    {
      "name": "Binary Search",
      "category": "algorithm",
      "description": "...",
      "confidence": 0.95,
      "evidence": "...",
      "relatedConcepts": ["Divide and Conquer"]
    }
  ],
  "visualizations": { "graph": {...}, "distribution": {...}, "cards": [...], "mermaid": "..." },
  "metrics": {
    "linesOfCode": 10,
    "functionsFound": 1,
    "classesFound": 0,
    "importsFound": 0,
    "conceptsExtracted": 3,
    "language": "python"
  },
  "processingTime": 1.234
}
```

---

### `POST /api/IT22601360/classify`
Quick rule-based classification (no AI, near-instant).

**Request:** `{ "code": "...", "language": "python" }`

**Response:**
```json
{
  "detectedPatterns": { "algorithms": ["binary_search"], "data_structures": [] },
  "primaryCategory": "algorithms",
  "confidence": 0.7,
  "processingTimeMs": 12.5
}
```

---

### `POST /api/IT22601360/concept-details`
Get a deep explanation of one concept using Gemini.

**Request:** `{ "conceptName": "Binary Search", "codeContext": "...", "detailLevel": "intermediate" }`

**Response:**
```json
{
  "success": true,
  "details": {
    "concept_name": "Binary Search",
    "definition": "...",
    "how_used_in_code": "...",
    "time_complexity": "O(log n)",
    "space_complexity": "O(1)",
    "advantages": ["Fast for sorted arrays"],
    "disadvantages": ["Requires sorted input"],
    "real_world_examples": ["Database indexing"],
    "related_concepts": ["Divide and Conquer"]
  }
}
```

---

### `GET /api/IT22601360/supported-languages`
Returns all supported programming languages.

**Response:** `{ "languages": ["python","javascript","typescript","java","cpp","c","csharp","go","rust","php","ruby"], "details": {...} }`

---

### `GET /api/IT22601360/health`
**Response:** `{ "status": "healthy", "component": "Code Concept Extractor", "student_id": "IT22601360", "gemini_available": true }`

---

## New Endpoints — Multi-File & Project Analysis

All three new endpoints return the **same response shape** (see "Common Project Response" below).

---

### `POST /api/IT22601360/extract-files`
Upload **multiple source files** via `multipart/form-data`.

**Content-Type:** `multipart/form-data`

**Form fields:**
| Field | Type | Required | Description |
|---|---|---|---|
| `files` | `File[]` | ✅ | One or more source code files |
| `language_override` | `string` | ❌ | Force a language for all files (e.g. `python`) |

**Limits:** Max 50 files, 5 MB per file.

**Frontend example (fetch):**
```javascript
const formData = new FormData();
formData.append('files', file1);
formData.append('files', file2);

const res = await fetch('http://localhost:8000/api/IT22601360/extract-files', {
  method: 'POST',
  body: formData,
});
const data = await res.json();
```

**Frontend example (axios):**
```javascript
const formData = new FormData();
files.forEach(f => formData.append('files', f));

const { data } = await axios.post(
  'http://localhost:8000/api/IT22601360/extract-files',
  formData,
  { headers: { 'Content-Type': 'multipart/form-data' } }
);
```

---

### `POST /api/IT22601360/extract-repo`
Clone a **GitHub repository** (shallow) and analyze all code files.

**Content-Type:** `application/json`

**Request:**
```json
{
  "repo_url": "https://github.com/TheAlgorithms/Python",
  "branch": "master",
  "language_filter": ["python", "javascript"]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `repo_url` | `string` | ✅ | HTTPS GitHub URL |
| `branch` | `string` | ❌ | Branch name (default: tries `main` then `master`) |
| `language_filter` | `string[]` | ❌ | Restrict to these languages. `null` = all |

**Response includes extra `repo_metadata` field:**
```json
{
  "repo_metadata": {
    "repoUrl": "https://github.com/...",
    "branch": "master",
    "totalFilesFound": 42,
    "languagesFound": ["python"]
  },
  ...commonProjectResponse
}
```

⚠️ **Note:** Large repos can take 30–60 seconds. Rate limits on Gemini apply.

---

### `POST /api/IT22601360/extract-local`
Scan a **local directory** on the server.

**Content-Type:** `application/json`

**Request:**
```json
{
  "directory_path": "D:/Projects/MyApp",
  "language_filter": ["python", "javascript"]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `directory_path` | `string` | ✅ | Absolute server-side path |
| `language_filter` | `string[]` | ❌ | Restrict to these languages. `null` = all |

---

## Common Project Response (for all 3 new endpoints)

```json
{
  "success": true,
  "totalProcessingTime": 5.123,

  "files": [
    {
      "filename": "binary_search.py",
      "language": "python",
      "success": true,
      "concepts": [
        {
          "name": "Binary Search",
          "category": "algorithm",
          "description": "...",
          "confidence": 0.95,
          "evidence": "...",
          "relatedConcepts": ["Divide and Conquer"]
        }
      ],
      "metrics": {
        "linesOfCode": 20,
        "functionsFound": 1,
        "classesFound": 0,
        "importsFound": 0,
        "conceptsExtracted": 3,
        "language": "python"
      },
      "processingTimeMs": 1200,
      "skipped": false,
      "skipReason": null
    },
    {
      "filename": "image.png",
      "language": "unknown",
      "success": false,
      "concepts": [],
      "metrics": {},
      "processingTimeMs": 0,
      "skipped": true,
      "skipReason": "Unsupported file extension"
    }
  ],

  "aggregated_concepts": [
    {
      "name": "Binary Search",
      "category": "algorithm",
      "description": "...",
      "confidence": 0.95,
      "evidence": "...",
      "relatedConcepts": ["Divide and Conquer"],
      "frequency": 3,
      "sourceFiles": ["binary_search.py", "search_utils.py"]
    }
  ],

  "project_summary": {
    "totalFilesScanned": 10,
    "totalFilesProcessed": 8,
    "totalFilesSkipped": 2,
    "totalLinesOfCode": 456,
    "languagesDetected": ["python", "javascript"],
    "totalConceptsExtracted": 27,
    "uniqueConcepts": 12,
    "topCategories": [
      { "category": "algorithm", "count": 5 },
      { "category": "data_structure", "count": 3 }
    ]
  }
}
```

---

## Concept Categories

| Value | Meaning |
|---|---|
| `algorithm` | Sorting, searching, recursion, DP, BFS, DFS… |
| `data_structure` | Array, linked list, stack, queue, tree, graph… |
| `design_pattern` | Singleton, factory, observer, strategy… |
| `architecture` | REST API, MVC, microservices, event-driven… |
| `paradigm` | OOP, functional, reactive, procedural… |
| `programming_concept` | Inheritance, closures, async/await, generics… |

---

## Error Responses

| Status | When |
|---|---|
| `400 Bad Request` | Invalid input (bad URL, no files, directory not found) |
| `422 Unprocessable Entity` | All files were skipped (no processable files found) |
| `500 Internal Server Error` | Unexpected extraction failure |
| `502 Bad Gateway` | Git clone failed (for `/extract-repo`) |
| `503 Service Unavailable` | Gemini API not configured |
