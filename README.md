# Insighta Labs Intelligence Query Engine

A FastAPI-based queryable intelligence engine for demographic profile data. Built for HNG Stage 2 Backend assessment.

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite (with indexes for performance)
- **Language**: Python 3.11+

## Setup & Running Locally

```bash
pip install -r requirements.txt

# Place seed_profiles.json in the project root, then:
uvicorn main:app --reload
```

API available at `http://localhost:8000`

---

## Endpoints

### `GET /api/profiles`

Returns paginated, filtered, and sorted profiles.

**Filters:**

| Parameter | Type | Description |
|---|---|---|
| `gender` | string | `male` or `female` |
| `age_group` | string | `child`, `teenager`, `adult`, `senior` |
| `country_id` | string | ISO 2-letter code e.g. `NG`, `KE` |
| `min_age` | int | Minimum age (inclusive) |
| `max_age` | int | Maximum age (inclusive) |
| `min_gender_probability` | float | Minimum gender confidence score |
| `min_country_probability` | float | Minimum country confidence score |
| `sort_by` | string | `age`, `created_at`, `gender_probability` |
| `order` | string | `asc` (default) or `desc` |
| `page` | int | Page number (default: 1) |
| `limit` | int | Results per page (default: 10, max: 50) |

**Example:**
```
GET /api/profiles?gender=male&country_id=NG&min_age=25&sort_by=age&order=desc&page=1&limit=10
```

**Response:**
```json
{
  "status": "success",
  "page": 1,
  "limit": 10,
  "total": 43,
  "data": [ ... ]
}
```

---

### `GET /api/profiles/search`

Natural language query endpoint. Rule-based parsing — no AI/LLMs used.

**Parameters:**

| Parameter | Description |
|---|---|
| `q` | Natural language query string |
| `page` | Page number (default: 1) |
| `limit` | Results per page (default: 10, max: 50) |

**Example queries:**

| Query | Parsed As |
|---|---|
| `young males from nigeria` | gender=male, min_age=16, max_age=24, country_id=NG |
| `females above 30` | gender=female, min_age=30 |
| `people from angola` | country_id=AO |
| `adult males from kenya` | gender=male, age_group=adult, country_id=KE |
| `male and female teenagers above 17` | age_group=teenager, min_age=17 |
| `seniors under 80` | age_group=senior, max_age=80 |
| `women between 20 and 40` | gender=female, min_age=20, max_age=40 |

**Uninterpretable query response:**
```json
{ "status": "error", "message": "Unable to interpret query" }
```

---

## Natural Language Parsing Logic

Rule-based keyword matching — no AI, no external APIs:

- **Gender**: matches `male/man/men/boy`, `female/woman/women/girl`
- **Age groups**: matches `child/kid`, `teen/teenager/adolescent`, `adult`, `senior/elderly/old`
- **"young"**: maps to `min_age=16, max_age=24` (not a stored age group)
- **Age modifiers**: `above/over/older than X` → `min_age`, `below/under X` → `max_age`, `between X and Y` → range
- **Country**: matches country names and adjectives to ISO codes (50+ countries supported)

---

## Database Schema

```sql
CREATE TABLE profiles (
    id TEXT PRIMARY KEY,              -- UUID v7
    name TEXT UNIQUE NOT NULL,
    gender TEXT NOT NULL,             -- "male" or "female"
    gender_probability REAL NOT NULL,
    age INTEGER NOT NULL,
    age_group TEXT NOT NULL,          -- child, teenager, adult, senior
    country_id TEXT NOT NULL,         -- ISO 2-letter code
    country_name TEXT NOT NULL,
    country_probability REAL NOT NULL,
    created_at TEXT NOT NULL
);
```

Indexes on `gender`, `age_group`, `country_id`, `age` for fast filtering.

---

## Error Responses

All errors follow:
```json
{ "status": "error", "message": "<error message>" }
```

| Status | Meaning |
|---|---|
| 400 | Missing or empty parameter |
| 422 | Invalid parameter type |
| 404 | Profile not found |
| 500/502 | Server failure |

## CORS

All origins allowed: `Access-Control-Allow-Origin: *`

## Deployment (Railway)

1. Push to GitHub (include `seed_profiles.json`)
2. Connect repo to [Railway](https://railway.app)
3. Railway auto-detects `Procfile` and deploys
4. Database seeds automatically on first startup
