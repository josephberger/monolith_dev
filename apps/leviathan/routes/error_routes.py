from flask import render_template

from apps.leviathan import app, api
from ..models import NotFoundError, ServerError


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html', error=error), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html', error=error), 500

@api.errorhandler(NotFoundError)
def handle_no_result_exception(error):
    '''Return a custom not found error message and 404 status code'''
    return error.to_dict(), 404

@api.errorhandler(Exception)
def default_error_handler(error):
    """Returns Internal server error"""
    error = ServerError()
    return error.to_dict()



