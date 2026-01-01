from flask import Blueprint, request, jsonify
from db.supabase import supabase
from collections import Counter

institution_bp = Blueprint("institution", __name__)

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
# 1️⃣ Institution autocomplete (AFTER country chosen)
# --------------------------------------------------
@institution_bp.route("/api/institutions/search", methods=["GET"])
def search_institutions_by_country():
    country_id = request.args.get("country_id")
    q = request.args.get("q", "").strip().lower()

    if not country_id:
        return jsonify({"error": "country_id is required"}), 400

    rows = (
        supabase
        .table("authorships")
        .select("""
            institution_info(
                id,
                name
            )
        """)
        .eq("country_id", country_id)
        .execute()
        .data or []
    )

    inst_map = {}
    for r in rows:
        inst = r.get("institution_info")
        if inst and (not q or q in inst["name"].lower()):
            inst_map[inst["id"]] = inst

    institutions = sorted(inst_map.values(), key=lambda x: x["name"])

    return jsonify(institutions[:10])


# --------------------------------------------------
# 2️⃣ Institution overview (stats card)
# --------------------------------------------------
@institution_bp.route("/api/institution/<institution_id>/overview", methods=["GET"])
def institution_overview(institution_id):
    institution = (
        supabase
        .table("institution_info")
        .select("id,name,average_h_index,average_rii,ranking")
        .eq("id", institution_id)
        .single()
        .execute()
        .data
    )

    return jsonify(institution)


# --------------------------------------------------
# 3️⃣ Research fields statistics for institution
# --------------------------------------------------
@institution_bp.route("/api/institution/<institution_id>/fields", methods=["GET"])
def institution_field_stats(institution_id):

    rows = (
        supabase
        .table("authorships")
        .select("article_id, articles(research_area_path)")
        .eq("institution_id", institution_id)
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

    return jsonify(stats[:10])  # top 10 domains

@institution_bp.route("/api/institutions/all", methods=["GET"])
def get_all_institutions():
    """Get top institutions with their stats"""
    # You might want to join with authorships to get aggregated data
    institutions = (
        supabase
        .table("institution_info")
        .select("id,name,average_h_index,average_rii,ranking")
        .order("ranking", desc=False)
        .limit(50)
        .execute()
        .data
    )
    return jsonify(institutions)

@institution_bp.route("/api/countries", methods=["GET"])
def get_all_countries():
    """Get unique countries from authorships"""
    authorships = (
        supabase
        .table("authorships")
        .select("country_id, country_info(name)")
        .execute()
        .data
    )
    
    # Extract unique countries
    country_map = {}
    for a in authorships:
        if a.get("country_info"):
            country_id = a["country_id"]
            country_name = a["country_info"]["name"]
            if country_id not in country_map:
                country_map[country_id] = {
                    "id": country_id,
                    "name": country_name
                }
    
    countries = list(country_map.values())
    countries.sort(key=lambda x: x["name"])
    
    return jsonify(countries)
