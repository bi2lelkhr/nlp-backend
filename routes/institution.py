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


# # --------------------------------------------------
# # 1️⃣ Institution autocomplete (AFTER country chosen)
# # --------------------------------------------------
# @institution_bp.route("/api/institutions/search", methods=["GET"])
# def search_institutions_by_country():
#     country_id = request.args.get("country_id")
#     q = request.args.get("q", "").strip().lower()

#     if not country_id:
#         return jsonify({"error": "country_id is required"}), 400

#     rows = (
#         supabase
#         .table("authorships")
#         .select("""
#             institution_info(
#                 id,
#                 name
#             )
#         """)
#         .eq("country_id", country_id)
#         .execute()
#         .data or []
#     )

#     inst_map = {}
#     for r in rows:
#         inst = r.get("institution_info")
#         if inst and (not q or q in inst["name"].lower()):
#             inst_map[inst["id"]] = inst

#     institutions = sorted(inst_map.values(), key=lambda x: x["name"])

#     return jsonify(institutions[:40])



@institution_bp.route("/api/institutions/search", methods=["GET"])
def search_institutions_by_country():
    country_id = request.args.get("country_id")
    q = request.args.get("q", "").strip().lower()

    if not country_id:
        return jsonify({"error": "country_id is required"}), 400

    # Get distinct institutions in that country
    rows = (
        supabase
        .table("authorships")
        .select("""
            institution_id,
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
        if not inst:
            continue

        name_l = inst["name"].lower()
        if q and q not in name_l:
            continue

        # Filter: ignore 0 or null averages
        avg_h = inst.get("average_h_index") or 0
        avg_rii = inst.get("average_rii") or 0
        if avg_h <= 0 and avg_rii <= 0:
            continue

        inst_map[inst["id"]] = {
            "id": inst["id"],
            "name": inst["name"],
            "average_h_index": avg_h,
            "average_rii": avg_rii,
            # no ranking at all
        }

    institutions = list(inst_map.values())
    # Sort by average_rii DESC (highest first)
    institutions.sort(key=lambda x: x["average_rii"], reverse=True)

    # You can still limit to 40 if you want
    return jsonify(institutions[:40])




# --------------------------------------------------
# 1️⃣ Institution overview
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

    return jsonify(institution or {})


# --------------------------------------------------
# 2️⃣ Institution field statistics (no indexes, no views)
# --------------------------------------------------
@institution_bp.route("/api/institution/<institution_id>/fields", methods=["GET"])
def institution_field_stats(institution_id):

    field_counter = Counter()
    total = 0

    page_size = 500
    offset = 0
    max_rows = 5000  # safety limit

    while offset < max_rows:

        rows = (
            supabase
            .table("authorships")
            .select("articles(research_area_path)")
            .eq("institution_id", institution_id)
            .range(offset, offset + page_size - 1)
            .execute()
            .data or []
        )

        if not rows:
            break

        for r in rows:
            article = r.get("articles")
            if not article:
                continue

            fields = normalize_fields(article.get("research_area_path"))
            for f in fields:
                field_counter[f] += 1
                total += 1

        offset += page_size

    stats = [
        {
            "field": field,
            "count": count,
            "percentage": round((count / total) * 100, 2) if total else 0
        }
        for field, count in field_counter.items()
    ]

    stats.sort(key=lambda x: x["count"], reverse=True)

    return jsonify(stats[:10])


# --------------------------------------------------
# 3️⃣ Get all institutions
# --------------------------------------------------
@institution_bp.route("/api/institutions/all", methods=["GET"])
def get_all_institutions():
    institutions = (
        supabase
        .table("institution_info")
        .select("id,name,average_h_index,average_rii")
        .execute()
        .data or []
    ) or []

    # Filter out 0 / null averages
    cleaned = []
    for inst in institutions:
        avg_h = inst.get("average_h_index") or 0
        avg_rii = inst.get("average_rii") or 0
        if avg_h <= 0 and avg_rii <= 0:
            continue
        cleaned.append({
            "id": inst["id"],
            "name": inst["name"],
            "average_h_index": avg_h,
            "average_rii": avg_rii,
        })

    cleaned.sort(key=lambda x: x["average_rii"], reverse=True)
    return jsonify(cleaned[:50])



# --------------------------------------------------
# 4️⃣ Get all countries (no full scan)
# --------------------------------------------------
@institution_bp.route("/api/countries", methods=["GET"])
def get_all_countries():

    page_size = 500
    offset = 0
    max_rows = 5000

    country_map = {}

    while offset < max_rows:

        rows = (
            supabase
            .table("authorships")
            .select("country_id, country_info(name)")
            .range(offset, offset + page_size - 1)
            .execute()
            .data or []
        )

        if not rows:
            break

        for r in rows:
            country = r.get("country_info")
            if not country:
                continue

            cid = r["country_id"]
            if cid not in country_map:
                country_map[cid] = {
                    "id": cid,
                    "name": country["name"]
                }

        offset += page_size

    countries = sorted(country_map.values(), key=lambda x: x["name"])

    return jsonify(countries)
