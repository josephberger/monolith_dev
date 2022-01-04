

class BaseError(Exception):
    """Base Error Class"""

    def __init__(self, code=400, message='Not Found', status='', field=None):
        Exception.__init__(self)
        self.code = code
        self.message = message
        self.status = status
        self.field = field

    def to_dict(self):
        return {'code': self.code,
                'message': self.message,
                'status': self.status,
                'field': self.field, }

class NotFoundError(BaseError):
    def __init__(self, message='Not found'):
        BaseError.__init__(self)
        self.code = 404
        self.message = message
        self.status = 'NOT_FOUND'

class ServerError(BaseError):
    def __init__(self, message='Internal server error'):
        BaseError.__init__(self)
        self.code = 500
        self.message = message
        self.status = 'SERVER_ERROR'