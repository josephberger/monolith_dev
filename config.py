import os
import logging.config

from models import ElasticIndex
from models import ESLogger
from redis import Redis
from rq import Queue
from rq.registry import FinishedJobRegistry


basedir = os.path.abspath(os.path.dirname(__file__))

#FLASK CONFIGS

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

#GLOBAL CONFIGS

class ElasticConfig(object):
    HOST = "localhost"
    PORT = 9200
    ENDPOINT_INDEX = "test"
    NMAP_INDEX = "nmap"
    VLAN_INDEX = "vlans"
    INTERFACE_INDEX = "interfaces"
    EP_DETAILS_INDEX = "ep_details"

class LogConfig(object):
    ES_HOST = "localhost"
    ES_PORT = 9200
    LOG_INDEX = ESLogger("logs", host=ES_HOST, port=ES_PORT)

class GlobalConfig(object):
    REDIS_HOST = "172.31.10.203"
    REDIS_PORT = 6379
    REDIS_CONNECTION = Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    HIGH_QUEUE = Queue(connection=REDIS_CONNECTION, name="high")
    DEFAULT_QUEUE = Queue(connection=REDIS_CONNECTION, name="default")

    CREDENTIALS = os.path.join('.credentials.yaml')

class LeviathanConfig(object):
    pass

#MONOLITH CONFIGS

# class LoggerConfig(object):
#     logging.config.fileConfig('settings/logging.conf')
#     LOGGER = logging.getLogger('application')
#     AUDITLOGGER = logging.getLogger('application')
#     es_log = logging.getLogger("elasticsearch")
#     netmiko_log = logging.getLogger("paramiko")
#     es_log.setLevel(logging.CRITICAL)
#     netmiko_log.setLevel(logging.CRITICAL)