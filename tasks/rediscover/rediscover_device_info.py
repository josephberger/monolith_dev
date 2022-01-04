from datetime import datetime

from config import GlobalConfig, LogConfig
from config import ElasticConfig
from models import ElasticIndex
from ctrl import discover
ENDPOINT_INDEX = ElasticIndex(ElasticConfig.ENDPOINT_INDEX, host=ElasticConfig.HOST, port=ElasticConfig.PORT)

LOG_INDEX = LogConfig.LOG_INDEX

def run(record):
    """ run task that will update device information ping->update
       ----------
           record:dict
               record from discover_device_info/retreive_device_info
       """

    #get local variables from the record dictionary
    ip = record['ip']
    record_id = record['_id']

    #determine of the device is reachable
    result = discover.discover_ping_check(ip)

    #run the update record method - send the job to redis high queue
    job = GlobalConfig.HIGH_QUEUE.enqueue(__update_device_info, args=(ip,record_id,), description=f"Update Device Info {ip}")

    #log the ping result to the elasticsearch log index
    if result:
        LOG_INDEX.generate_log(message=f"ping response from {ip} - Starting job {job.id}", process="rediscover")
    else:
        LOG_INDEX.generate_log(message=f"no ping response from {ip} - Starting job {job.id}", process="rediscover")

def __update_device_info(ip,record_id):
    """ record the device information after the ping check returns true
       ----------
            ip:str
               ip address of target device
            record_id: str
                elasticsearch _id value

        """

    record = discover.discover_device_info(ip, GlobalConfig.CREDENTIALS)
    record['update_time'] = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    #update document in elasticsearch based on fields and the _id value
    ENDPOINT_INDEX.update_document(record_id=record_id, updates=record)

    #log the result to the elasticsearch log index
    if record['device_type'] == "unknown":
        LOG_INDEX.generate_log(message=f"unable to determine credentials and device_type for {ip}",process="record_device_info")
        return
    else:
        LOG_INDEX.generate_log(message=f"device_type for {ip} discovered: {record['device_type']}", process="record_device_info")