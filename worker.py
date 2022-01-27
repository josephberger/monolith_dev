import os
import redis
from rq import Worker, Queue, Connection

from config import Config
from redis import Redis
appconfig = Config()

redis_host = appconfig.REDIS_HOST
redis_port = appconfig.REDIS_PORT
redis_connection = Redis(host=redis_host, port=redis_port, db=0)
high_queue = Queue(connection=redis_connection, name="high")
default_queue = Queue(connection=redis_connection, name="default")

listen = ['default']
conn_redis = redis.from_url('redis://172.31.10.203:6379')

if __name__ == '__main__':

    with Connection(conn_redis):
        worker = Worker(list(map(Queue, listen)))

    worker.work()
