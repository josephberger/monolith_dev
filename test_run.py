import ipaddress
from rq.job import Job
from tasks.leviathan import sweep

from config import GlobalConfig

for ip in ipaddress.IPv4Network("172.31.10.0/24"):
    # job = Job.create(sweep.run,
    #                  args=(str(ip),),
    #                  kwargs={
    #                      'description': f'Sweep {str(ip)}',
    #                  })
    #
    # #GlobalConfig.DEFAULT_QUEUE.enqueue(job)

    result = GlobalConfig.DEFAULT_QUEUE.enqueue(sweep.run,
                                                args=(str(ip),),
                                                description= f'Sweep {str(ip)}')
