from flask import Blueprint, jsonify
from db.supabase import supabase

overview_bp = Blueprint("overview", __name__)

# --------------------------------------------------
# COUNTRIES OVERVIEW
# --------------------------------------------------
@overview_bp.route("/api/overview/countries", methods=["GET"])
def overview_countries():
    by_h = (
        supabase
        .table("country_info")
        .select("id,name,average_h_index")
        .order("average_h_index", desc=True)
        .limit(10)
        .execute()
        .data or []
    )

    by_rii = (
        supabase
        .table("country_info")
        .select("id,name,average_rii")
        .order("average_rii", desc=True)
        .limit(10)
        .execute()
        .data or []
    )

    total = (
        supabase
        .table("country_info")
        .select("id", count="exact")
        .execute()
        .count or 0
    )

    return jsonify({
        "total": total,
        "by_h_index": by_h,
        "by_rii": by_rii
    })


# --------------------------------------------------
# INSTITUTIONS OVERVIEW
# --------------------------------------------------
@overview_bp.route("/api/overview/institutions", methods=["GET"])
def overview_institutions():
    by_h = (
        supabase
        .table("institution_info")
        .select("id,name,average_h_index")
        .order("average_h_index", desc=True)
        .limit(10)
        .execute()
        .data or []
    )

    by_rii = (
        supabase
        .table("institution_info")
        .select("id,name,average_rii")
        .order("average_rii", desc=True)
        .limit(10)
        .execute()
        .data or []
    )

    total = (
        supabase
        .table("institution_info")
        .select("id", count="exact")
        .execute()
        .count or 0
    )

    return jsonify({
        "total": total,
        "by_h_index": by_h,
        "by_rii": by_rii
    })


# --------------------------------------------------
# RESEARCHERS OVERVIEW
# --------------------------------------------------
@overview_bp.route("/api/overview/researchers", methods=["GET"])
def overview_researchers():
    by_h = (
        supabase
        .table("researchers")
        .select("id,full_name,h_index")
        .order("h_index", desc=True)
        .limit(10)
        .execute()
        .data or []
    )

    by_rii = (
        supabase
        .table("researchers")
        .select("id,full_name,rii")
        .order("rii", desc=True)
        .limit(10)
        .execute()
        .data or []
    )

    total = (
        supabase
        .table("researchers")
        .select("id", count="exact")
        .execute()
        .count or 0
    )

    return jsonify({
        "total": total,
        "by_h_index": by_h,
        "by_rii": by_rii
    })


# --------------------------------------------------
# FIELDS OVERVIEW (derived from articles)
# --------------------------------------------------
@overview_bp.route("/api/overview/fields", methods=["GET"])
def overview_fields():
    rows = (
        supabase
        .table("articles")
        .select("research_area_path")
        .execute()
        .data or []
    )

    field_set = set()

    for r in rows:
        path = r.get("research_area_path")
        if not path:
            continue
        parts = [p.strip().lower() for p in path.split(">") if p.strip()]
        field_set.update(parts)

    return jsonify({
        "total": len(field_set)
    })


# --------------------------------------------------
# GLOBAL OVERVIEW (ALL COUNTS IN ONE CALL)
# --------------------------------------------------
@overview_bp.route("/api/overview/stats", methods=["GET"])
def overview_stats():
    researchers = (
        supabase.table("researchers")
        .select("id", count="exact")
        .execute()
        .count or 0
    )

    countries = (
        supabase.table("country_info")
        .select("id", count="exact")
        .execute()
        .count or 0
    )

    institutions = (
        supabase.table("institution_info")
        .select("id", count="exact")
        .execute()
        .count or 0
    )

    rows = (
        supabase
        .table("articles")
        .select("research_area_path")
        .execute()
        .data or []
    )

    field_set = set()
    for r in rows:
        if r.get("research_area_path"):
            field_set.update(
                p.strip().lower()
                for p in r["research_area_path"].split(">")
                if p.strip()
            )

    return jsonify({
        "researchers": researchers,
        "countries": countries,
        "institutions": institutions,
        "fields": len(field_set)
    })
