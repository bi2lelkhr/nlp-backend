# from flask import Flask
# from flask_cors import CORS
# from routes.articles import articles_bp
# from routes.analytics import analytics_bp
# from routes.researchers import researcher_bp
# from routes.overview import overview_bp
# from routes.institution import institution_bp
# from routes.country import country_bp
# from routes.field import field_bp


# app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": "*"}})

# app.register_blueprint(institution_bp)
# app.register_blueprint(analytics_bp)
# app.register_blueprint(researcher_bp)
# app.register_blueprint(overview_bp)
# app.register_blueprint(country_bp)
# app.register_blueprint(field_bp)

# if __name__ == "__main__":
#     app.run(debug=True)

from flask import Flask
from flask_cors import CORS

from routes.articles import articles_bp
from routes.analytics import analytics_bp
from routes.researchers import researcher_bp
from routes.overview import overview_bp
from routes.institution import institution_bp
from routes.country import country_bp
from routes.field import field_bp

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.register_blueprint(institution_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(researcher_bp)
app.register_blueprint(overview_bp)
app.register_blueprint(country_bp)
app.register_blueprint(field_bp)


if __name__ == "__main__":
    app.run()
