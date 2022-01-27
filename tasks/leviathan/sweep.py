from datetime import datetime
import logging

from models import ElasticIndex
from redis import Redis
from rq import Queue
from decouple import config as envconf
from config import Config
from ctrl import Discover


appconfig = Config()
discover = Discover(appconfig)

#redis configuration
redis_host = appconfig.REDIS_HOST
redis_port = appconfig.REDIS_PORT
redis_connection = Redis(host=redis_host, port=redis_port, db=0)

#elastic configuration
elastic_host = appconfig.ELASTIC_HOST
elastic_port = appconfig.ELASTIC_PORT
endpoint_index = appconfig.ENDPOINT_INDEX
nmap_index = appconfig.NMAP_INDEX

#logging configuration
# logging.basicConfig(filename="var/log/system.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
#                     datefmt='%Y-%m-%d %H:%M:%S')


def run(ip):
    """ initial run method for the entire task
       ----------
           ip:str
               ip address of target device
       """

    queue = Queue(connection=redis_connection, name="high")

    result = discover.ping(ip)
    if result:
        job = queue.enqueue(__record_device_info, args=(ip,), description=f"Record Device Info {ip}")
        logging.info(f"ping response from {ip} - Starting job {job.id}")


def __record_device_info(ip):
    """ record the device information after the ping check returns true
       ----------
            ip:str
               ip address of target device
       """

    index = ElasticIndex(endpoint_index,host=elastic_host, port=elastic_port)
    queue = Queue(connection=redis_connection, name="high")

    record = discover.device_info(ip)
    record['update_time'] = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    #record device in elasticsearch device index
    index.add_document(record)

    #add the nmap scan to the high queue
    queue.enqueue(__record_nmap_info, args=(record,), description=f"Record NMAP Info {ip}")

    if record['device_type'] == "unknown":
        logging.info(f"unable to determine credentials and device_type for {ip}")
        return
    else:
        logging.info(f"device_type for {ip} discovered: {record['device_type']}")

        if record['device_type'] in appconfig.PLUGIN_MODS:
            plugin_module = appconfig.PLUGINS[record['device_type']]
            queue.enqueue(plugin_module.record_details, args=(record,appconfig),
                                            description=f"Record {record['device_type']} info {ip}")

def __record_nmap_info(record):
    """ record the device information after the ping check returns true
       ----------
        record:dict
           record from __record_device_info
   """
    index = ElasticIndex(nmap_index, host=elastic_host, port=elastic_port)

    scan_info = discover.nmap_info(record['ip'],record['hostname'])

    index.add_document(scan_info)
    logging.info("nmap scanned device {record['ip']}")