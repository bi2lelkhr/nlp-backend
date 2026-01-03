from flask import Blueprint, request, jsonify
from db.supabase import supabase
from collections import Counter

country_bp = Blueprint("country", __name__)

# --------------------------------------------------
# Helper: normalize research field
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
# 1️⃣ Country autocomplete (type → closest match)
# --------------------------------------------------
@country_bp.route("/api/countries/search", methods=["GET"])
def search_countries():
    q = request.args.get("q", "").strip().lower()

    query = supabase.table("country_info").select("id,name")

    if q:
        query = query.ilike("name", f"%{q}%")

    countries = (
        query
        .order("name")
        .limit(10)
        .execute()
        .data or []
    )

    return jsonify(countries)


# --------------------------------------------------
# 2️⃣ Country overview (stats card)
# --------------------------------------------------
@country_bp.route("/api/country/<country_id>/overview", methods=["GET"])
def country_overview(country_id):
    country = (
        supabase
        .table("country_info")
        .select("id,name,average_h_index,average_rii,ranking")
        .eq("id", country_id)
        .single()
        .execute()
        .data
    )

    return jsonify(country)


# --------------------------------------------------
# 3️⃣ Best institutions for a country
# --------------------------------------------------
@country_bp.route("/api/country/<country_id>/institutions", methods=["GET"])
def country_best_institutions(country_id):
    rows = (
        supabase
        .table("authorships")
        .select("""
            institution_info(
                id,
                name,
                average_h_index,
                average_rii
            )
        """)
        .eq("country_id", country_id)
        .execute()
        .data or []
    )

    inst_map = {}
    for r in rows:
        inst = r.get("institution_info")
        if inst:
            inst_map[inst["id"]] = inst

    institutions = list(inst_map.values())

    return jsonify({
        "by_h_index": sorted(
            institutions,
            key=lambda x: x["average_h_index"],
            reverse=True
        )[:5],
        "by_rii": sorted(
            institutions,
            key=lambda x: x["average_rii"],
            reverse=True
        )[:5]
    })


# --------------------------------------------------
# 4️⃣ Research fields statistics (percentages)
# --------------------------------------------------
@country_bp.route("/api/country/<country_id>/fields", methods=["GET"])
def country_field_stats(country_id):

    rows = (
        supabase
        .table("authorships")
        .select("article_id, articles(research_area_path)")
        .eq("country_id", country_id)
        .execute()
        .data or []
    )

    field_counter = Counter()
    total = 0

    for r in rows:
        article = r.get("articles")
        if not article:
            continue

        fields = normalize_fields(article.get("research_area_path"))
        for f in fields:
            field_counter[f] += 1
            total += 1

    stats = [
        {
            "field": k,
            "count": v,
            "percentage": round((v / total) * 100, 2) if total else 0
        }
        for k, v in field_counter.items()
    ]

    stats.sort(key=lambda x: x["count"], reverse=True)

    return jsonify(stats[:10])  # top 10 research domains

@country_bp.route("/api/countries", methods=["GET"])
def get_all_countries():
    """Get all countries"""
    countries = (
        supabase
        .table("country_info")
        .select("id, name")
        .order("name")
        .execute()
        .data
    )
    return jsonify(countries or [])
