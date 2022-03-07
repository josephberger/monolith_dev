import ipaddress

from redis import Redis
from rq import Queue

from config import Config
from tasks.leviathan import sweep

appconfig = Config()

redis_host = appconfig.REDIS_HOST
redis_port = appconfig.REDIS_PORT
redis_connection = Redis(host=redis_host, port=redis_port, db=0)
high_queue = Queue(connection=redis_connection, name="high")
default_queue = Queue(connection=redis_connection, name="default")


for ip in ipaddress.IPv4Network("172.31.5.0/24"):
    result = default_queue.enqueue(sweep.run,
                                   args=(str(ip),),
                                   description=f'Sweep {str(ip)}')

for ip in ipaddress.IPv4Network("172.31.10.0/24"):
    result = default_queue.enqueue(sweep.run,
                                   args=(str(ip),),
                                   description=f'Sweep {str(ip)}')
