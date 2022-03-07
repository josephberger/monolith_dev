from redis import Redis
from rq import Worker, Queue, Connection

from config import Config

appconfig = Config()

redis_host = appconfig.REDIS_HOST
redis_port = appconfig.REDIS_PORT
redis_connection = Redis(host=redis_host, port=redis_port, db=0)

listen = ['high']

if __name__ == '__main__':

    with Connection(redis_connection):
        worker = Worker([Queue('high')])

    worker.work()
