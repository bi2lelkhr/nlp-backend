from flask import Blueprint, request, jsonify
from db.supabase import supabase
from collections import Counter, defaultdict

researcher_bp = Blueprint("researcher", __name__)

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
# 1️⃣ Researcher autocomplete (type → closest name)
# --------------------------------------------------
# @researcher_bp.route("/api/researchers/search", methods=["GET"])
# def search_researchers():
#     q = request.args.get("q", "").strip().lower()

#     query = supabase.table("researchers").select("id,full_name")

#     if q:
#         query = query.ilike("full_name", f"%{q}%")

#     researchers = (
#         query
#         .order("full_name")
#         .limit(10)
#         .execute()
#         .data or []
#     )

#     return jsonify(researchers)


# --------------------------------------------------
# 2️⃣ Researcher overview (profile info)
# --------------------------------------------------
@researcher_bp.route("/api/researcher/<researcher_id>/overview", methods=["GET"])
def researcher_overview(researcher_id):
    researcher = (
        supabase
        .table("researchers")
        .select("""
            id,
            full_name,
            orcid,
            h_index,
            rii,
            total_publications,
            total_citations
        """)
        .eq("id", researcher_id)
        .single()
        .execute()
        .data
    )

    return jsonify(researcher)


# --------------------------------------------------
# 3️⃣ Researcher articles
# --------------------------------------------------
@researcher_bp.route("/api/researcher/<researcher_id>/articles", methods=["GET"])
def researcher_articles(researcher_id):
    rows = (
        supabase
        .table("authorships")
        .select("""
            articles(
                id,
                title,
                publication_date,
                journal_name,
                cited_by_count
            )
        """)
        .eq("researcher_id", researcher_id)
        .execute()
        .data or []
    )

    articles = [r["articles"] for r in rows if r.get("articles")]
    return jsonify(articles)


# --------------------------------------------------
# 4️⃣ Co-author network
# --------------------------------------------------
# @researcher_bp.route("/api/researcher/<researcher_id>/coauthors", methods=["GET"])
# def researcher_coauthors(researcher_id):

#     # articles written by researcher
#     article_rows = (
#         supabase
#         .table("authorships")
#         .select("article_id")
#         .eq("researcher_id", researcher_id)
#         .execute()
#         .data or []
#     )

#     article_ids = [r["article_id"] for r in article_rows]
#     if not article_ids:
#         return jsonify([])

#     rows = (
#         supabase
#         .table("authorships")
#         .select("""
#             researcher_id,
#             researchers(
#                 id,
#                 full_name,
#                 h_index,
#                 rii
#             )
#         """)
#         .in_("article_id", article_ids)
#         .neq("researcher_id", researcher_id)
#         .execute()
#         .data or []
#     )

#     coauthor_counter = defaultdict(int)
#     coauthors = {}

#     for r in rows:
#         res = r.get("researchers")
#         if res:
#             coauthor_counter[res["id"]] += 1
#             coauthors[res["id"]] = res

#     result = [
#         {
#             "id": rid,
#             "name": coauthors[rid]["full_name"],
#             "h_index": coauthors[rid]["h_index"],
#             "rii": coauthors[rid]["rii"],
#             "shared_articles": coauthor_counter[rid]
#         }
#         for rid in coauthors
#     ]

#     result.sort(key=lambda x: x["shared_articles"], reverse=True)

#     return jsonify(result)



@researcher_bp.route("/api/researcher/<researcher_id>/coauthors", methods=["GET"])
def researcher_coauthors(researcher_id):

    row = (
        supabase
        .table("researchers")
        .select("full_name, co_authorship")
        .eq("id", researcher_id)
        .single()
        .execute()
    )

    data = row.data
    if not data or not data.get("co_authorship"):
        return jsonify([])

    researcher_name = data["full_name"].strip()

    coauthors = [
        name.strip()
        for name in data["co_authorship"].split("/")
        if name.strip() and name.strip() != researcher_name
    ]

    result = [
        {
            "name": name
        }
        for name in sorted(set(coauthors))
    ]

    return jsonify(result)



# --------------------------------------------------
# 5️⃣ Research fields contribution (percentages)
# --------------------------------------------------
# @researcher_bp.route("/api/researcher/<researcher_id>/fields", methods=["GET"])
# def researcher_field_stats(researcher_id):

#     rows = (
#         supabase
#         .table("authorships")
#         .select("articles(research_area_path)")
#         .eq("researcher_id", researcher_id)
#         .execute()
#         .data or []
#     )

#     field_counter = Counter()
#     total = 0

#     for r in rows:
#         article = r.get("articles")
#         if not article:
#             continue

#         fields = normalize_fields(article.get("research_area_path"))
#         for f in fields:
#             field_counter[f] += 1
#             total += 1

#     stats = [
#         {
#             "field": k,
#             "count": v,
#             "percentage": round((v / total) * 100, 2) if total else 0
#         }
#         for k, v in field_counter.items()
#     ]

#     stats.sort(key=lambda x: x["count"], reverse=True)

#     return jsonify(stats)


@researcher_bp.route("/api/researcher/<researcher_id>/fields", methods=["GET"])
def researcher_field_stats(researcher_id):

    rows = (
        supabase
        .table("authorships")
        .select("articles(research_area_path)")
        .eq("researcher_id", researcher_id)
        .execute()
        .data or []
    )

    field_counter = Counter()
    total = 0

    for r in rows:
        article = r.get("articles")
        if not article:
            continue

        path = article.get("research_area_path")
        if not path:
            continue

        # ---- LEAF EXTRACTION ----
        leaf_field = path.split(">")[-1].strip()

        field_counter[leaf_field] += 1
        total += 1

    stats = [
        {
            "field": field,
            "count": count,
            "percentage": round((count / total) * 100, 2) if total else 0
        }
        for field, count in field_counter.items()
    ]

    stats.sort(key=lambda x: x["count"], reverse=True)

    return jsonify(stats[:5])





# --------------------------------------------------
# 6️⃣ Top 5 researchers (h-index vs RII comparison)
# --------------------------------------------------
@researcher_bp.route("/api/researchers/top5/hindex-rii", methods=["GET"])
def top5_researchers_hindex_rii():
    rows = (
        supabase
        .table("researchers")
        .select("""
            id,
            full_name,
            h_index,
            rii
        """)
        .order("h_index", desc=True)
        .order("rii", desc=True)
        .limit(5)
        .execute()
        .data or []
    )

    result = [
        {
            "id": r["id"],
            "name": r["full_name"],
            "h_index": r["h_index"],
            "rii": float(r["rii"])
        }
        for r in rows
    ]

    return jsonify(result)

# Add this new endpoint to get all researchers with pagination
@researcher_bp.route("/api/researchers/all", methods=["GET"])
def get_all_researchers():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    offset = (page - 1) * limit

    # Get total count
    count_res = (
        supabase
        .table("researchers")
        .select("id", count="exact")
        .execute()
    )
    total_count = count_res.count

    # Get paginated researchers
    researchers = (
        supabase
        .table("researchers")
        .select("id,full_name,h_index,rii,total_publications,total_citations")
        .order("h_index", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
        .data or []
    )

    return jsonify({
        "researchers": researchers,
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": (total_count + limit - 1) // limit
    })

# Update the search endpoint to search from first letter
@researcher_bp.route("/api/researchers/search", methods=["GET"])
def search_researchers():
    q = request.args.get("q", "").strip().lower()
    
    if not q:
        return jsonify([])
    
    # Search for researchers whose name starts with the search term
    # Then also include researchers whose name contains the search term
    query = supabase.table("researchers").select("id,full_name")
    
    # First try exact start match
    start_match = (
        query
        .ilike("full_name", f"{q}%")
        .order("full_name")
        .limit(10)
        .execute()
        .data or []
    )
    
    # If we have less than 10, add contains matches
    if len(start_match) < 10:
        contains_match = (
            supabase
            .table("researchers")
            .select("id,full_name")
            .ilike("full_name", f"%{q}%")
            .order("full_name")
            .limit(10 - len(start_match))
            .execute()
            .data or []
        )
        
        # Combine results, avoiding duplicates
        start_ids = {r["id"] for r in start_match}
        combined = start_match.copy()
        for r in contains_match:
            if r["id"] not in start_ids:
                combined.append(r)
        
        return jsonify(combined[:10])
    
    return jsonify(start_match[:10])
