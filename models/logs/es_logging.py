import json
from datetime import datetime
from elasticsearch import Elasticsearch
import pytz

class ESLoggerException(Exception):
    pass

class ESLogger():

    def __init__(self, index="logs", host="localhost", port="9200", auth=None):

        self.es_connection = Elasticsearch([{'host': host, 'port': port}])
        self.index = index

    def generate_log(self, message, level=6, process='default'):

        if type(level) != int:
            raise(ESLoggerException("level must be an int between 0 and 7"))

        if level > 7 or level < 0:
            raise (ESLoggerException("level must be an int between 0 and 7"))

        #generate the timestamp
        date_time_obj = datetime.strptime(str(datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f%z')),
                                          '%Y-%m-%dT%H:%M:%S.%f')
        timezone = pytz.timezone('America/New_York')
        timezone_date_time_obj = timezone.localize(date_time_obj)

        log_message = {
            'process': process,
            'level': level,
            '@timestamp': timezone_date_time_obj.strftime('%Y-%m-%dT%H:%M:%S.%f%z'),
            'message': message
        }

        self.es_connection.index(index=self.index, ignore=400, body=json.dumps(log_message))