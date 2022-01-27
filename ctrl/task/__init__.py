from redis import Redis
from rq import Queue

from .actions import rediscover_device_info, rediscover_nmap_info, rediscover_vlan_info, remove_endpoint_info, \
    rediscover_interface_info


class TaskMgr:
    def __init__(self, appconfig):
        
        redis_host = appconfig.REDIS_HOST
        redis_port = appconfig.REDIS_PORT
        redids_connection = Redis(host=redis_host, port=redis_port, db=0)
        self.high_queue = Queue(connection=redids_connection, name='high')
        
        self.appconfig = appconfig

    def rediscover_device_info(self,record):

        job = self.high_queue.enqueue(rediscover_device_info.run,
                                   args=(record,self.appconfig,),
                                   description=f"Rediscover info {record['ip']}")
        return job

    def rediscover_nmap_info(self,record):

        job = self.high_queue.enqueue(rediscover_nmap_info.run,
                                   args=(record,self.appconfig,),
                                   description=f"Rediscover nmap {record['ip']}")
        return job

    def rediscover_vlan_info(self,record):

        job = self.high_queue.enqueue(rediscover_vlan_info.run,
                                   args=(record,self.appconfig,),
                                   description=f"Rediscover vlan {record['ip']}")
        return job

    def rediscover_interface_info(self,record):

        job = self.high_queue.enqueue(rediscover_interface_info.run,
                                   args=(record,self.appconfig,),
                                   description=f"Rediscover interfaces {record['ip']}")
        return job

    def remove_endpoint_info(self, record):

        job = self.high_queue.enqueue(remove_endpoint_info.run,
                                   args=(record, self.appconfig,),
                                   description=f"Delete {record['ip']}")

        return job
