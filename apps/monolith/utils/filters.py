"""Filters
"""

from apps.monolith import app

@app.template_filter('is_list')
def is_list(value):
    return isinstance(value, list)