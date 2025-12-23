from flask import Blueprint, request, jsonify
from db.supabase import supabase
from collections import Counter

field_bp = Blueprint("field", __name__)

# --------------------------------------------------
# Helper: normalize research fields
# --------------------------------------------------
def normalize_fields(path: str):
    """
    'Computer Science > Quantum Computing'
    → ['computer science', 'quantum computing']
    """
    if not path:
        return []
    return [p.strip().lower() for p in path.split(">") if p.strip()]


# --------------------------------------------------
# 1️⃣ Extract ALL existing fields (unique)
# --------------------------------------------------
@field_bp.route("/api/fields/search", methods=["GET"])
def search_fields():
    q = request.args.get("q", "").strip().lower()

    rows = (
        supabase
        .table("articles")
        .select("research_area_path")
        .execute()
        .data or []
    )

    field_set = set()
    for r in rows:
        fields = normalize_fields(r.get("research_area_path"))
        for f in fields:
            if not q or q in f:
                field_set.add(f)

    results = sorted(field_set)
    return jsonify(results[:15])


# --------------------------------------------------
# 2️⃣ Best researchers in a field
# --------------------------------------------------
@field_bp.route("/api/field/overview", methods=["GET"])
def field_overview():
    field = request.args.get("field")
    if not field:
        return jsonify({"error": "field is required"}), 400

    field = field.strip().lower()

    # Get articles that contain this field
    articles = (
        supabase
        .table("articles")
        .select("id,research_area_path")
        .execute()
        .data or []
    )

    article_ids = [
        a["id"]
        for a in articles
        if field in normalize_fields(a.get("research_area_path"))
    ]

    if not article_ids:
        return jsonify({
            "by_h_index": [],
            "by_rii": []
        })

    rows = (
        supabase
        .table("authorships")
        .select("""
            researcher_id,
            researchers(
                id,
                full_name,
                h_index,
                rii
            )
        """)
        .in_("article_id", article_ids)
        .execute()
        .data or []
    )

    researcher_map = {}
    for r in rows:
        res = r.get("researchers")
        if res:
            researcher_map[res["id"]] = res

    researchers = list(researcher_map.values())

    return jsonify({
        "by_h_index": sorted(
            researchers,
            key=lambda x: x["h_index"],
            reverse=True
        )[:3],
        "by_rii": sorted(
            researchers,
            key=lambda x: x["rii"],
            reverse=True
        )[:3]
    })

# --------------------------------------------------
# 3️⃣ Country contribution in a field
# --------------------------------------------------
@field_bp.route("/api/field/countries", methods=["GET"])
def field_country_contribution():
    field = request.args.get("field")
    if not field:
        return jsonify({"error": "field is required"}), 400

    field = field.strip().lower()

    # 1️⃣ Find articles matching the field
    articles = (
        supabase
        .table("articles")
        .select("id,research_area_path")
        .execute()
        .data or []
    )

    article_ids = [
        a["id"]
        for a in articles
        if field in normalize_fields(a.get("research_area_path"))
    ]

    if not article_ids:
        return jsonify([])

    # 2️⃣ Get authorships with country info
    rows = (
        supabase
        .table("authorships")
        .select("""
            country_id,
            country_info(
                id,
                name,
                iso_code
            )
        """)
        .in_("article_id", article_ids)
        .execute()
        .data or []
    )

    # 3️⃣ Count contributions per country
    country_counter = Counter()
    country_meta = {}

    for r in rows:
        country = r.get("country_info")
        if country:
            cid = country["id"]
            country_counter[cid] += 1
            country_meta[cid] = country

    total = sum(country_counter.values())

    # 4️⃣ Build response
    result = [
        {
            "country_id": cid,
            "country": country_meta[cid]["name"],
            "iso_code": country_meta[cid]["iso_code"],
            "count": count,
            "percentage": round((count / total) * 100, 2) if total else 0
        }
        for cid, count in country_counter.items()
    ]

    # Sort by contribution
    result.sort(key=lambda x: x["count"], reverse=True)

    return jsonify(result)


# --------------------------------------------------
# 4️⃣ Best researchers in a field FOR a specific country
# --------------------------------------------------
@field_bp.route("/api/field/country/researchers", methods=["GET"])
def field_country_researchers():
    field = request.args.get("field")
    country_id = request.args.get("country_id")

    if not field or not country_id:
        return jsonify({"error": "field and country_id are required"}), 400

    field = field.strip().lower()

    # 1️⃣ Find articles matching the field
    articles = (
        supabase
        .table("articles")
        .select("id,research_area_path")
        .execute()
        .data or []
    )

    article_ids = [
        a["id"]
        for a in articles
        if field in normalize_fields(a.get("research_area_path"))
    ]

    if not article_ids:
        return jsonify([])

    # 2️⃣ Get researchers in that field + country
    rows = (
        supabase
        .table("authorships")
        .select("""
            researcher_id,
            researchers(
                id,
                full_name,
                h_index,
                rii,
                total_publications,
                total_citations
            )
        """)
        .eq("country_id", country_id)
        .in_("article_id", article_ids)
        .execute()
        .data or []
    )

    researcher_map = {}
    for r in rows:
        res = r.get("researchers")
        if res:
            researcher_map[res["id"]] = res

    researchers = list(researcher_map.values())

    return jsonify({
        "by_h_index": sorted(researchers, key=lambda x: x["h_index"], reverse=True)[:5],
        "by_rii": sorted(researchers, key=lambda x: x["rii"], reverse=True)[:5]
    })
