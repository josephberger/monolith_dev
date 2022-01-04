import ipaddress
from rq.job import Job
from tasks.leviathan import sweep

from config import GlobalConfig

# for ip in ipaddress.IPv4Network("172.31.5.0/24"):
#
#     result = GlobalConfig.DEFAULT_QUEUE.enqueue(sweep.run,
#                                                 args=(str(ip),),
#                                                 description= f'Sweep {str(ip)}')

for ip in ipaddress.IPv4Network("172.31.10.0/24"):

    result = GlobalConfig.DEFAULT_QUEUE.enqueue(sweep.run,
                                                args=(str(ip),),
                                                description= f'Sweep {str(ip)}')
