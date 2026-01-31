# ATS Optimizer & CV Preview - API Specification

## Core Principles (MANDATORY)

1. **Original CV is Inviolable** - Never modify, overwrite, or hide the original
2. **Full Transparency** - Every score, issue, and change must be explained
3. **Separate Versions** - Original and optimized CVs are distinct entities
4. **Trust Through Clarity** - System behavior is obvious and predictable

---

## Endpoint 1: ATS Analysis (Score Breakdown)

### POST `/api/cv/ats-score`

Analyze CV and return detailed ATS compatibility breakdown.

**Request:**

```json
{
  "cv_data": {
    "personal_info": {...},
    "work_experience": [...],
    "education": [...],
    "personal_skills": {...},
    "summary": "..."
  }
}
```

**Response (200 OK):**

```json
{
  "overall_score": 75,
  "grade": "B",

  "score_breakdown": {
    "keyword_match": {
      "score": 18,
      "max": 25,
      "percentage": 72.0,
      "details": [
        "Found 12/15 common tech keywords",
        "Keywords detected: python, react, sql, docker, git",
        "Missing: kubernetes, microservices, ci/cd"
      ]
    },
    "skills_alignment": {
      "score": 20,
      "max": 25,
      "details": [
        "✅ Well-organized skills into 4 categories",
        "✅ Good number of skills listed (18)"
      ]
    },
    "experience_relevance": {
      "score": 19,
      "max": 25,
      "details": [
        "❌ Job 1: Weak verb 'worked' in description",
        "✅ Job 1: Uses strong action verbs in other sections",
        "✅ Job 1: Includes quantifiable metrics"
      ]
    },
    "formatting_compatibility": {
      "score": 18,
      "max": 25,
      "details": [
        "✅ All standard sections present",
        "⚠️ Some special characters detected"
      ]
    }
  },

  "issues": [
    {
      "category": "experience_relevance",
      "severity": "critical",
      "message": "Weak verb 'worked' in Job 1 description"
    },
    {
      "category": "keyword_match",
      "severity": "warning",
      "message": "Missing 3 key industry keywords"
    }
  ],

  "recommendations": {
    "critical": [
      "Replace weak verb 'worked' with stronger action verb",
      "Add missing keywords: kubernetes, microservices, ci/cd"
    ],
    "high": ["Expand skills section with more relevant technologies"],
    "medium": ["Reduce special characters in formatting"],
    "low": []
  }
}
```

---

## Endpoint 2: Generate ATS-Optimized CV (With Transparency)

### POST `/api/cv/generate-ats-optimized`

Create a separate, optimized CV version while keeping original untouched.

**Request:**

```json
{
  "cv_data": {
    "personal_info": {...},
    "work_experience": [...],
    "education": [...],
    "personal_skills": {...}
  }
}
```

**Response (200 OK):**

```json
{
  "original_cv": {
    "personal_info": {...},
    "work_experience": [
      {
        "job_title": "Software Engineer",
        "description": "Worked with databases"
      }
    ],
    "education": [...],
    "personal_skills": {...}
  },

  "optimized_cv": {
    "personal_info": {...},
    "work_experience": [
      {
        "job_title": "Software Engineer",
        "description": "Designed and optimized PostgreSQL databases"
      }
    ],
    "education": [...],
    "personal_skills": {...}
  },

  "original_analysis": {
    "overall_score": 65,
    "grade": "C",
    "score_breakdown": {...},
    "issues": [...],
    "recommendations": {...}
  },

  "optimized_analysis": {
    "overall_score": 78,
    "grade": "B",
    "score_breakdown": {...},
    "issues": [...],
    "recommendations": {...}
  },

  "changes": [
    {
      "field": "work_experience[0].description",
      "before": "Worked with databases",
      "after": "Designed and optimized PostgreSQL databases",
      "reason": "Improves keyword recognition and skill specificity. 'Designed' is a stronger action verb that better describes database architecture work."
    },
    {
      "field": "work_experience[1].description",
      "before": "Was responsible for API development",
      "after": "Led development of microservices APIs with FastAPI",
      "reason": "More specific, stronger action verb. Includes key technology names for better keyword matching."
    }
  ],

  "score_improvement": 13,
  "transparency_note": "All changes shown above with before/after/reason. Original CV never modified."
}
```

---

## CV Preview: Show Original Document

### GET `/api/cv/{user_id}/preview`

Return the original uploaded CV file.

**Response (200 OK):**

```json
{
  "original_file_url": "https://storage.example.com/cvs/john-doe-cv.pdf",
  "file_name": "john-doe-cv.pdf",
  "file_type": "application/pdf",
  "rendered": true,
  "note": "This is the exact document you uploaded. No modifications."
}
```

---

## Forbidden Behaviors

❌ **DO NOT:**

- Return only a score without explanation
- Hide the original CV
- Show parsed text instead of the uploaded file
- Silently apply optimizations
- Invent experience or skills
- Overwrite the original
- Omit the "reason" field from changes
- Return empty results without explanation

✅ **ALWAYS:**

- Show both original and optimized versions
- Explain every score with a breakdown
- List all changes with before/after/reason
- Keep the original untouched
- Provide actionable, specific recommendations
- Return meaningful error messages

---

## Frontend Integration Guide

### 1. Display ATS Score with Breakdown

```jsx
// Call /api/cv/ats-score to get detailed analysis
const analysisResponse = await fetch("/api/cv/ats-score", {
  method: "POST",
  body: JSON.stringify({ cv_data }),
});

const analysis = await analysisResponse.json();

// Display score breakdown
<div>
  <h3>
    ATS Compatibility: {analysis.overall_score}/100 ({analysis.grade})
  </h3>

  <div>
    <h4>Score Breakdown:</h4>
    {Object.entries(analysis.score_breakdown).map(([category, data]) => (
      <div key={category}>
        <p>
          {category}: {data.score}/{data.max} ({data.percentage.toFixed(1)}%)
        </p>
        <ul>
          {data.details.map((detail) => (
            <li key={detail}>{detail}</li>
          ))}
        </ul>
      </div>
    ))}
  </div>

  <div>
    <h4>Issues Found:</h4>
    <ul>
      {analysis.issues.map((issue, i) => (
        <li key={i} className={`severity-${issue.severity}`}>
          {issue.message}
        </li>
      ))}
    </ul>
  </div>

  <div>
    <h4>Recommendations:</h4>
    {Object.entries(analysis.recommendations).map(([priority, items]) => (
      <div key={priority}>
        <h5>{priority.toUpperCase()}</h5>
        <ul>
          {items.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      </div>
    ))}
  </div>
</div>;
```

### 2. Show Optimized CV with Changes

```jsx
// Call /api/cv/generate-ats-optimized
const response = await fetch("/api/cv/generate-ats-optimized", {
  method: "POST",
  body: JSON.stringify({ cv_data }),
});

const { original_cv, optimized_cv, changes, score_improvement } =
  await response.json();

// Display side-by-side comparison
<div>
  <h3>ATS Optimization</h3>
  <p>Score Improvement: +{score_improvement} points</p>

  <h4>Changes Made ({changes.length}):</h4>
  {changes.map((change, i) => (
    <div key={i} className="change-card">
      <div>
        <label>Before:</label>
        <p className="before">{change.before}</p>
      </div>
      <div>
        <label>After:</label>
        <p className="after">{change.after}</p>
      </div>
      <div>
        <label>Reason:</label>
        <p className="reason">{change.reason}</p>
      </div>
    </div>
  ))}

  <button onClick={() => downloadCVVersion(optimized_cv)}>
    Download ATS-Optimized CV
  </button>
</div>;
```

### 3. CV Preview (Show Original File)

```jsx
// Display original uploaded PDF/image
<div className="cv-preview">
  <div className="version-selector">
    <button className="selected">Original CV</button>
    <button>ATS-Optimized CV</button>
  </div>

  <div className="preview-container">
    {/* Embed original PDF */}
    <embed src={cv.original_file_url} type="application/pdf" />
  </div>
</div>
```

---

## Error Handling

All endpoints follow this pattern for errors:

**400 Bad Request:**

```json
{
  "detail": "CV data is required"
}
```

**404 Not Found:**

```json
{
  "detail": "CV not found for user 14"
}
```

**500 Internal Server Error:**

```json
{
  "detail": "Failed to calculate ATS score: [reason]"
}
```

**NEVER** return empty results. **ALWAYS** explain why something failed.

---

## Data Storage Model

```python
class CV(Base):
    # ========== ORIGINAL CV ==========
    original_file_url: str  # URL to uploaded PDF/image
    original_file_name: str  # Original filename

    # ========== PARSED DATA ==========
    json_content: dict  # Parsed from original

    # ========== ATS ANALYSIS ==========
    ats_score: float  # 0-100
    ats_grade: str  # A+, A, B, C, D
    ats_analysis: dict  # Detailed breakdown
    ats_issues: list  # Issues found
    ats_recommendations: list  # Recommendations

    # ========== ATS OPTIMIZATION ==========
    ats_optimized_content: dict  # Separate version
    ats_changes: list  # [{"before": ..., "after": ..., "reason": ...}]
    ats_optimized_at: datetime  # When created
```

---

## Success Criteria Checklist

- ✅ User can view original CV exactly as uploaded
- ✅ ATS score is fully explained with breakdown
- ✅ All ATS changes are visible with before/after/reason
- ✅ Original and optimized CVs are separate
- ✅ System behavior builds trust and clarity
- ✅ No silent modifications or hidden data
- ✅ No invented experience or skills
- ✅ All errors explained with actionable guidance
