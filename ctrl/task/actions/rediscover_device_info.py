from datetime import datetime
import logging
from models import ElasticIndex
from ctrl import Discover

def run(record, appconfig):
    """ record the device information
   ----------
    record:dict
       record from discover_device_info
    envconf: decouple.config
        environmental variables
    """

    discover = Discover(appconfig)

    # elastic configuration
    elastic_host = appconfig.ELASTIC_HOST
    elastic_port = appconfig.ELASTIC_PORT
    endpoint_index = appconfig.ENDPOINT_INDEX

    #variables extracted from record
    ip = record['ip']
    record_id = record['_id']

    #update the record via discovery
    new_record = discover.device_info(ip)
    #add an update_time
    new_record['update_time'] = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    #set the index
    index = ElasticIndex(endpoint_index, elastic_host, elastic_port)

    #update document in elasticsearch based on fields and the _id value
    index.update_document(record_id=record_id, updates=new_record)

    #log the result
    if record['device_type'] == "unknown":
        logging.info(f"unable to determine credentials and device_type for {ip}")
    else:
        logging.info(f"device_type for {ip} re-discovered: {new_record['device_type']}")