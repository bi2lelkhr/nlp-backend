from flask import Blueprint, request, jsonify
from db.supabase import supabase

analytics_bp = Blueprint("analytics", __name__)

# --------------------------------------------------
# Helper
# --------------------------------------------------
def avg(values):
    return round(sum(values) / len(values), 2) if values else 0


# --------------------------------------------------
# MAIN ANALYTICS ENDPOINT
# --------------------------------------------------
@analytics_bp.route("/analytics", methods=["GET"])
def analytics():
    country_id = request.args.get("country_id")
    institution_id = request.args.get("institution_id")
    field = request.args.get("field")

    if institution_id and not country_id:
        return jsonify({"error": "country_id is required when institution_id is provided"}), 400

    # --------------------------------------------------
    # 1️⃣ FILTER ARTICLES BY FIELD
    # --------------------------------------------------
    article_ids = None

    if field:
        field_normalized = " ".join(field.strip().lower().split())

        articles = (
            supabase
            .table("articles")
            .select("id")
            .ilike("research_area_path", f"%{field_normalized}%")
            .execute()
            .data
        )

        article_ids = [a["id"] for a in articles]

        if not article_ids:
            return jsonify({
                "filters": {
                    "country_id": country_id,
                    "institution_id": institution_id,
                    "field": field
                },
                "metrics": {
                    "average_h_index": 0,
                    "average_rii": 0
                },
                "top_researchers": {
                    "by_h_index": [],
                    "by_rii": []
                },
                "top_institutions": None
            })

    # --------------------------------------------------
    # 2️⃣ QUERY AUTHORSHIPS
    # --------------------------------------------------
    query = (
        supabase
        .table("authorships")
        .select("""
            researcher_id,
            institution_id,
            country_id,
            researchers(
                id,
                full_name,
                h_index,
                rii,
                total_publications,
                total_citations
            ),
            institution_info(
                id,
                name,
                average_h_index,
                average_rii
            )
        """)
    )

    if article_ids:
        query = query.in_("article_id", article_ids)

    if country_id:
        query = query.eq("country_id", country_id)

    if institution_id:
        query = query.eq("institution_id", institution_id)

    rows = query.execute().data or []

    # --------------------------------------------------
    # 3️⃣ AGGREGATION
    # --------------------------------------------------
    researcher_map = {}
    institution_map = {}

    for row in rows:
        r = row.get("researchers")
        inst = row.get("institution_info")

        if r:
            researcher_map[r["id"]] = {
                "id": r["id"],
                "name": r["full_name"],
                "h_index": r["h_index"],
                "rii": r["rii"],
                "total_publications": r["total_publications"],
                "total_citations": r["total_citations"]
            }

        if inst:
            institution_map[inst["id"]] = {
                "id": inst["id"],
                "name": inst["name"],
                "average_h_index": inst["average_h_index"],
                "average_rii": inst["average_rii"]
            }

    researchers = list(researcher_map.values())
    institutions = list(institution_map.values())

    # --------------------------------------------------
    # 4️⃣ METRICS
    # --------------------------------------------------
    metrics = {
        "average_h_index": avg([r["h_index"] for r in researchers]),
        "average_rii": avg([r["rii"] for r in researchers])
    }

    # --------------------------------------------------
    # 5️⃣ TOP RESEARCHERS
    # --------------------------------------------------
    top_researchers = {
        "by_h_index": sorted(researchers, key=lambda x: x["h_index"], reverse=True)[:10],
        "by_rii": sorted(researchers, key=lambda x: x["rii"], reverse=True)[:10]
    }

    # --------------------------------------------------
    # 6️⃣ TOP INSTITUTIONS (ONLY WHEN COUNTRY LEVEL)
    # --------------------------------------------------
    top_institutions = None
    if country_id and not institution_id:
        top_institutions = {
            "by_h_index": sorted(institutions, key=lambda x: x["average_h_index"], reverse=True)[:10],
            "by_rii": sorted(institutions, key=lambda x: x["average_rii"], reverse=True)[:10]
        }

    return jsonify({
        "filters": {
            "country_id": country_id,
            "institution_id": institution_id,
            "field": field
        },
        "metrics": metrics,
        "top_researchers": top_researchers,
        "top_institutions": top_institutions
    })


@analytics_bp.route("/api/countries", methods=["GET"])
def get_countries():
    countries = supabase.table("country_info").select("id,name").execute().data or []
    return jsonify(countries)

# -------------------------------
# Institutions endpoint
# -------------------------------
@analytics_bp.route("/api/institutions", methods=["GET"])
def get_institutions():
    institutions = supabase.table("institution_info").select("id,name").execute().data or []
    return jsonify(institutions)