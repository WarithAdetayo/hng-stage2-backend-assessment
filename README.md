# Insighta Labs Intelligence Query Engine

A FastAPI-based queryable intelligence engine for demographic profile data. Built for HNG Stage 2 Backend assessment.

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite (with indexes for query performance)
- **Language**: Python 3.11+
- **NLP**: Rule-based keyword parsing (no AI, no LLMs)

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

Returns paginated, filtered, and sorted profiles. All filters are combinable — results must match **all** applied conditions.

**Query Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `gender` | string | `male` or `female` |
| `age_group` | string | `child`, `teenager`, `adult`, `senior` |
| `country_id` | string | ISO 2-letter code e.g. `NG`, `KE` |
| `min_age` | int | Minimum age (inclusive) |
| `max_age` | int | Maximum age (inclusive) |
| `min_gender_probability` | float | Minimum gender confidence score (0.0–1.0) |
| `min_country_probability` | float | Minimum country confidence score (0.0–1.0) |
| `sort_by` | string | `age`, `created_at`, or `gender_probability` |
| `order` | string | `asc` (default) or `desc` |
| `page` | int | Page number, default `1`, minimum `1` |
| `limit` | int | Results per page, default `10`, max `50` |

**Example:**
```
GET /api/profiles?gender=male&country_id=NG&min_age=25&sort_by=age&order=desc&page=1&limit=10
```

**Success Response:**
```json
{
  "status": "success",
  "page": 1,
  "limit": 10,
  "total": 43,
  "data": [
    {
      "id": "019dbd13-3cd8-7325-8483-bc1f68df97c5",
      "name": "Chukwuemeka Obi",
      "gender": "male",
      "gender_probability": 0.95,
      "age": 34,
      "age_group": "adult",
      "country_id": "NG",
      "country_name": "Nigeria",
      "country_probability": 0.82,
      "created_at": "2026-04-24T01:20:47Z"
    }
  ]
}
```

---

### `GET /api/profiles/search`

Natural language query endpoint. Converts plain English into structured filters. Rule-based parsing — no AI or LLMs used.

**Query Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `q` | string | Natural language query (required) |
| `page` | int | Page number, default `1` |
| `limit` | int | Results per page, default `10`, max `50` |

**Example:**
```
GET /api/profiles/search?q=young males from nigeria&page=1&limit=10
```

**Example queries and how they are parsed:**

| Query | Parsed Filters |
|---|---|
| `young males from nigeria` | gender=male, min_age=16, max_age=24, country_id=NG |
| `females above 30` | gender=female, min_age=30 |
| `people from angola` | country_id=AO |
| `adult males from kenya` | gender=male, age_group=adult, country_id=KE |
| `male and female teenagers above 17` | age_group=teenager, min_age=17 |
| `seniors under 80` | age_group=senior, max_age=80 |
| `women between 20 and 40` | gender=female, min_age=20, max_age=40 |
| `children from ghana` | age_group=child, country_id=GH |
| `elderly women over 60` | age_group=senior, gender=female, min_age=60 |

**Uninterpretable query — 400 response:**
```json
{ "status": "error", "message": "Unable to interpret query" }
```

---

## Natural Language Parsing Logic

The NLP module (`nlp.py`) uses pure regex-based keyword matching with no external dependencies. Here is exactly how each part works:

### Gender Detection
Scans for gender keywords using word-boundary regex (`\b`):
- **male**: `male`, `man`, `men`, `boy`, `boys`, `males`
- **female**: `female`, `woman`, `women`, `girl`, `girls`, `females`

### Age Group Detection
Maps keywords to stored age group values:
- **child**: `child`, `children`, `kids`, `kid`
- **teenager**: `teenager`, `teenagers`, `teen`, `teens`, `adolescent`
- **adult**: `adult`, `adults`
- **senior**: `senior`, `seniors`, `elderly`, `old`

### "young" Keyword
`young` is **not** a stored age group. It maps to `min_age=16, max_age=24` for parsing purposes only.

### Age Modifiers
Regex patterns extract numeric age constraints:
- `above X` / `over X` / `older than X` → `min_age = X`
- `below X` / `under X` / `younger than X` → `max_age = X`
- `between X and Y` → `min_age = X`, `max_age = Y`
- `aged X` / `age X` → exact age match (`min_age = X`, `max_age = X`)

### Country Detection
A dictionary of 50+ country names and adjectives maps to ISO 2-letter codes. Multi-word countries (e.g. "south africa") are matched first (longest match wins):
- `nigeria` / `nigerian` → `NG`
- `kenya` / `kenyan` → `KE`
- `angola` / `angolan` → `AO`
- `south africa` / `south african` → `ZA`
- *(and 46+ more)*

If none of these patterns match anything in the query, the endpoint returns `"Unable to interpret query"` with HTTP 400.

---

## Database Schema

```sql
CREATE TABLE profiles (
    id TEXT PRIMARY KEY,              -- UUID v7 (time-ordered)
    name TEXT UNIQUE NOT NULL,        -- Full name, unique per record
    gender TEXT NOT NULL,             -- "male" or "female"
    gender_probability REAL NOT NULL, -- 0.0 to 1.0
    age INTEGER NOT NULL,
    age_group TEXT NOT NULL,          -- child, teenager, adult, senior
    country_id TEXT NOT NULL,         -- ISO 2-letter code e.g. NG
    country_name TEXT NOT NULL,       -- Full country name
    country_probability REAL NOT NULL,-- 0.0 to 1.0
    created_at TEXT NOT NULL          -- UTC ISO 8601
);
```

**Indexes** on `gender`, `age_group`, `country_id`, `age` — avoids full table scans on common filter columns.

**Seeding**: On startup, if the table is empty, all 2026 profiles from `seed_profiles.json` are inserted using `INSERT OR IGNORE` to prevent duplicates on re-runs.

---

## Error Responses

All errors follow this structure:
```json
{ "status": "error", "message": "<error message>" }
```

| Status Code | Trigger |
|---|---|
| `400` | Missing/empty parameter, uninterpretable NL query, invalid pagination |
| `422` | Invalid parameter type (non-int for age, etc.) |
| `404` | Profile not found |
| `500/502` | Server or database failure |

## CORS

All origins allowed on every response: `Access-Control-Allow-Origin: *`

---

## Deployment (Railway)

1. Push this repo to GitHub — include `seed_profiles.json`
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Railway auto-detects the `Procfile` and sets `$PORT`
4. The database creates itself and seeds all 2026 profiles on first startup — no manual steps needed
