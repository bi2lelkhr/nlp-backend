from flask import Blueprint, request, jsonify
from db.supabase import supabase

articles_bp = Blueprint("articles", __name__)


@articles_bp.route("/articles", methods=["GET"])
def get_articles():
    response = supabase.table("articles").select("*").execute()
    return jsonify(response.data)
