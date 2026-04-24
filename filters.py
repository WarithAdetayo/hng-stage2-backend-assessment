import sqlite3
from typing import Optional, Tuple, List, Dict, Any


ALLOWED_SORT = {"age", "created_at", "gender_probability"}


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "gender": row["gender"],
        "gender_probability": row["gender_probability"],
        "age": row["age"],
        "age_group": row["age_group"],
        "country_id": row["country_id"],
        "country_name": row["country_name"],
        "country_probability": row["country_probability"],
        "created_at": row["created_at"],
    }


def build_filter_query(
    db: sqlite3.Connection,
    filters: Dict[str, Any],
    sort_by: Optional[str],
    order: str,
    page: int,
    limit: int,
) -> Tuple[List[Dict], int]:
    conditions = []
    params = []

    if filters.get("gender"):
        conditions.append("gender = ?")
        params.append(filters["gender"])

    if filters.get("age_group"):
        conditions.append("age_group = ?")
        params.append(filters["age_group"])

    if filters.get("country_id"):
        conditions.append("country_id = ?")
        params.append(filters["country_id"].upper())

    if filters.get("min_age") is not None:
        conditions.append("age >= ?")
        params.append(filters["min_age"])

    if filters.get("max_age") is not None:
        conditions.append("age <= ?")
        params.append(filters["max_age"])

    if filters.get("min_gender_probability") is not None:
        conditions.append("gender_probability >= ?")
        params.append(filters["min_gender_probability"])

    if filters.get("min_country_probability") is not None:
        conditions.append("country_probability >= ?")
        params.append(filters["min_country_probability"])

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    # Count total
    count_sql = f"SELECT COUNT(*) FROM profiles {where_clause}"
    total = db.execute(count_sql, params).fetchone()[0]

    # Sorting
    order_clause = ""
    if sort_by and sort_by in ALLOWED_SORT:
        direction = "DESC" if order == "desc" else "ASC"
        order_clause = f"ORDER BY {sort_by} {direction}"

    # Pagination
    offset = (page - 1) * limit
    data_sql = f"SELECT * FROM profiles {where_clause} {order_clause} LIMIT ? OFFSET ?"

    rows = db.execute(data_sql, params + [limit, offset]).fetchall()
    return [row_to_dict(r) for r in rows], total
