from app import app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Response
import serverless_wsgi

def handler(event, context):
    return serverless_wsgi.handle_request(app, event, context)
