import os
from redis import Redis
from rq import Worker, Queue, Connection

listen = ['default']
redis_connection = Redis(host='172.31.10.203', port=6379, db=0)

if __name__ == '__main__':

    with Connection(redis_connection):
        worker = Worker([Queue('default')])

    worker.work()
