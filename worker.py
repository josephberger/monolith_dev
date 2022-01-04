import os
import redis
from rq import Worker, Queue, Connection

listen = ['default']
conn_redis = redis.from_url('redis://172.31.10.203:6379')

if __name__ == '__main__':

    with Connection(conn_redis):
        worker = Worker(list(map(Queue, listen)))

    worker.work()