from flask import Blueprint, request, jsonify
from db.supabase import supabase
from collections import Counter

field_bp = Blueprint("field", __name__)


# --------------------------------------------------
# Helper: normalize research fields
# --------------------------------------------------
def normalize_fields(path: str):
    if not path:
        return []
    return [p.strip().lower() for p in path.split(">") if p.strip()]


# --------------------------------------------------
# Helper: get article ids for a field using server-side filtering
# --------------------------------------------------
def get_articles_with_field(field: str, max_ids: int | None = None):
    """
    Fetch article ids whose research_area_path contains a given normalized field.
    Uses pagination with server-side ilike filtering to avoid full table scans.
    """
    field = field.strip().lower()
    if not field:
        return []

    page = 0
    page_size = 1000
    ids: list[int] = []

    # Use ilike on research_area_path so Postgres does the filtering.
    # You can improve this further with a generated column and index in SQL.
    while True:
        res = (
            supabase
            .table("articles")
            .select("id, research_area_path")
            .ilike("research_area_path", f"%{field}%")
            .range(page * page_size, (page + 1) * page_size - 1)
            .execute()
        )
        rows = res.data or []
        if not rows:
            break

        for r in rows:
            # Extra safety: still normalize client-side to avoid false positives
            if field in normalize_fields(r.get("research_area_path")):
                ids.append(r["id"])

        if max_ids is not None and len(ids) >= max_ids:
            return ids[:max_ids]

        page += 1

    return ids


# --------------------------------------------------
# Helper: chunk a list into smaller lists
# --------------------------------------------------
def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]


# --------------------------------------------------
# 1️⃣ Search all fields (cached-ish & lighter)
# --------------------------------------------------
@field_bp.route("/api/fields/search", methods=["GET"])
def search_fields():
    q = request.args.get("q", "").strip().lower()
    field_set = set()
    page = 0
    page_size = 2000  # bigger page reduces round-trips

    while True:
        res = (
            supabase
            .table("articles")
            .select("research_area_path")
            .range(page * page_size, (page + 1) * page_size - 1)
            .execute()
        )
        rows = res.data or []
        if not rows:
            break

        for r in rows:
            for f in normalize_fields(r.get("research_area_path")):
                if not q or q in f:
                    field_set.add(f)

        page += 1

    # For very large sets you might want to limit results here
    return jsonify(sorted(field_set))


# --------------------------------------------------
# 2️⃣ Best researchers in a field (server-side group)
# --------------------------------------------------
@field_bp.route("/api/field/overview", methods=["GET"])
def field_overview():
    field = request.args.get("field")
    if not field:
        return jsonify({"error": "field is required"}), 400

    # We only care about distinct researchers and their metrics, not every authorship row.
    # So: fetch article_ids (limited) then query authorships joined to researchers.
    article_ids = get_articles_with_field(field, max_ids=20000)
    if not article_ids:
        return jsonify({"by_h_index": [], "by_rii": []})

    # To reduce duplicates, we keep a map in Python but we don't bring extra columns.
    researcher_map = {}

    for chunk in chunked(article_ids, 500):
        res = (
            supabase
            .table("authorships")
            .select(
                """
                researcher_id,
                researchers (
                    id,
                    full_name,
                    h_index,
                    rii
                )
                """
            )
            .in_("article_id", chunk)
            .execute()
        )
        rows = res.data or []
        for r in rows:
            rs = r.get("researchers")
            if rs:
                rid = rs["id"]
                # Keep the "best" record if duplicates appear with nulls
                existing = researcher_map.get(rid)
                if existing is None:
                    researcher_map[rid] = rs
                else:
                    # Prefer non-null metrics
                    if existing.get("h_index") is None and rs.get("h_index") is not None:
                        researcher_map[rid] = rs
                    elif existing.get("rii") is None and rs.get("rii") is not None:
                        researcher_map[rid] = rs

    researchers = list(researcher_map.values())

    # Filter out null metrics to avoid weird ordering
    by_h_index = [
        r for r in researchers if r.get("h_index") is not None
    ]
    by_rii = [
        r for r in researchers if r.get("rii") is not None
    ]

    by_h_index_sorted = sorted(
        by_h_index,
        key=lambda x: (x["h_index"], x["id"]),
        reverse=True
    )[:6]

    by_rii_sorted = sorted(
        by_rii,
        key=lambda x: (x["rii"], x["id"]),
        reverse=True
    )[:6]

    return jsonify({
        "by_h_index": by_h_index_sorted,
        "by_rii": by_rii_sorted,
    })


# --------------------------------------------------
# 3️⃣ Country contribution (lighter aggregation)
# --------------------------------------------------
@field_bp.route("/api/field/countries", methods=["GET"])
def field_country_contribution():
    field = request.args.get("field")
    if not field:
        return jsonify({"error": "field is required"}), 400

    article_ids = get_articles_with_field(field, max_ids=20000)
    if not article_ids:
        return jsonify([])

    all_rows = []
    for chunk in chunked(article_ids, 500):
        res = (
            supabase
            .table("authorships")
            .select(
                """
                country_id,
                country_info (
                    id,
                    name,
                    iso_code
                )
                """
            )
            .in_("article_id", chunk)
            .execute()
        )
        all_rows.extend(res.data or [])

    country_counter = Counter()
    country_meta = {}
    for r in all_rows:
        country = r.get("country_info")
        if country:
            cid = country["id"]
            country_counter[cid] += 1
            country_meta[cid] = country

    total = sum(country_counter.values()) or 1

    result = [
        {
            "country_id": cid,
            "country": country_meta[cid]["name"],
            "iso_code": country_meta[cid]["iso_code"],
            "count": count,
            "percentage": round((count / total) * 100, 2),
        }
        for cid, count in country_counter.items()
        if country_meta.get(cid)  # defensive
    ]

    result.sort(key=lambda x: x["count"], reverse=True)
    return jsonify(result)


# --------------------------------------------------
# 4️⃣ Best researchers in a field for a country (filtered + dedup)
# --------------------------------------------------
@field_bp.route("/api/field/country/researchers", methods=["GET"])
def field_country_researchers():
    field = request.args.get("field")
    country_id = request.args.get("country_id")
    if not field or not country_id:
        return jsonify({"error": "field and country_id are required"}), 400

    article_ids = get_articles_with_field(field, max_ids=20000)
    if not article_ids:
        return jsonify([])

    researcher_map = {}

    for chunk in chunked(article_ids, 500):
        res = (
            supabase
            .table("authorships")
            .select(
                """
                researcher_id,
                country_id,
                researchers (
                    id,
                    full_name,
                    h_index,
                    rii,
                    total_publications,
                    total_citations
                )
                """
            )
            .eq("country_id", country_id)
            .in_("article_id", chunk)
            .execute()
        )
        rows = res.data or []
        for r in rows:
            rs = r.get("researchers")
            if rs:
                rid = rs["id"]
                # Deduplicate same researcher across many articles
                existing = researcher_map.get(rid)
                if existing is None:
                    researcher_map[rid] = rs
                else:
                    # Prefer non-null metrics
                    if existing.get("h_index") is None and rs.get("h_index") is not None:
                        researcher_map[rid] = rs
                    elif existing.get("rii") is None and rs.get("rii") is not None:
                        researcher_map[rid] = rs

    researchers = list(researcher_map.values())

    by_h_index = [
        r for r in researchers if r.get("h_index") is not None
    ]
    by_rii = [
        r for r in researchers if r.get("rii") is not None
    ]

    by_h_index_sorted = sorted(
        by_h_index,
        key=lambda x: (x["h_index"], x["id"]),
        reverse=True
    )[:8]

    by_rii_sorted = sorted(
        by_rii,
        key=lambda x: (x["rii"], x["id"]),
        reverse=True
    )[:8]

    return jsonify({
        "by_h_index": by_h_index_sorted,
        "by_rii": by_rii_sorted,
    })
