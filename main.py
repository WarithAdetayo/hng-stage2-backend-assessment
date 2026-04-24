from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from typing import Optional
from database import get_db, init_db
from filters import build_filter_query
from nlp import parse_natural_language
import uvicorn

app = FastAPI(title="Insighta Labs Intelligence Query Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    init_db()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"status": "error", "message": "Invalid query parameters"},
        headers={"Access-Control-Allow-Origin": "*"},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {"status": "error", "message": exc.detail}
    return JSONResponse(
        status_code=exc.status_code,
        content=detail,
        headers={"Access-Control-Allow-Origin": "*"},
    )


@app.get("/api/profiles")
def get_profiles(
    gender: Optional[str] = None,
    age_group: Optional[str] = None,
    country_id: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    min_gender_probability: Optional[float] = None,
    min_country_probability: Optional[float] = None,
    sort_by: Optional[str] = Query(None, regex="^(age|created_at|gender_probability)$"),
    order: Optional[str] = Query("asc", regex="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
):
    # Validate pagination explicitly for clean error envelope
    if page < 1 or limit < 1 or limit > 50:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Invalid query parameters"},
            headers={"Access-Control-Allow-Origin": "*"},
        )

    # Validate enums
    if gender and gender not in ("male", "female"):
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Invalid query parameters"},
            headers={"Access-Control-Allow-Origin": "*"},
        )
    if age_group and age_group not in ("child", "teenager", "adult", "senior"):
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Invalid query parameters"},
            headers={"Access-Control-Allow-Origin": "*"},
        )

    filters = {
        "gender": gender,
        "age_group": age_group,
        "country_id": country_id.upper() if country_id else None,
        "min_age": min_age,
        "max_age": max_age,
        "min_gender_probability": min_gender_probability,
        "min_country_probability": min_country_probability,
    }

    db = get_db()
    try:
        rows, total = build_filter_query(db, filters, sort_by, order, page, limit)
    finally:
        db.close()

    return JSONResponse(
        content={
            "status": "success",
            "page": page,
            "limit": limit,
            "total": total,
            "data": rows,
        },
        headers={"Access-Control-Allow-Origin": "*"},
    )


@app.get("/api/profiles/search")
def search_profiles(
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
):
    if not q or not q.strip():
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Missing or empty 'q' query parameter"},
            headers={"Access-Control-Allow-Origin": "*"},
        )

    if page < 1 or limit < 1 or limit > 50:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Invalid query parameters"},
            headers={"Access-Control-Allow-Origin": "*"},
        )

    filters = parse_natural_language(q.strip())

    if filters is None:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Unable to interpret query"},
            headers={"Access-Control-Allow-Origin": "*"},
        )

    db = get_db()
    try:
        rows, total = build_filter_query(db, filters, None, "asc", page, limit)
    finally:
        db.close()

    return JSONResponse(
        content={
            "status": "success",
            "page": page,
            "limit": limit,
            "total": total,
            "data": rows,
        },
        headers={"Access-Control-Allow-Origin": "*"},
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
