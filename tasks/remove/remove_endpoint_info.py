from datetime import datetime

from config import GlobalConfig, LogConfig
from config import ElasticConfig
from models import ElasticIndex
from ctrl import discover
ENDPOINT_INDEX = ElasticIndex(ElasticConfig.ENDPOINT_INDEX, host=ElasticConfig.HOST, port=ElasticConfig.PORT)
NMAP_INDEX = ElasticIndex(ElasticConfig.NMAP_INDEX, host=ElasticConfig.HOST, port=ElasticConfig.PORT)
VLAN_INDEX = ElasticIndex(ElasticConfig.VLAN_INDEX, host=ElasticConfig.HOST, port=ElasticConfig.PORT)
INTERFACE_INDEX = ElasticIndex(ElasticConfig.INTERFACE_INDEX,
                               host=ElasticConfig.HOST,
                               port=ElasticConfig.PORT)

LOG_INDEX = LogConfig.LOG_INDEX

def run(record):
    """ run task that removes all the information associated with an endpoint
       ----------
           record:dict
               record from discover_device_info/retreive_device_info
       """

    #get local variables from the record dictionary
    hostname = record['hostname']
    record_id = record['_id']

    #remove the endpoint info from the endpoint index
    ENDPOINT_INDEX.remove_document_by_id(doc_id=record_id)
    LOG_INDEX.generate_log(message=f"Deleted {hostname} endpoint information", process="remove")

    #run the nmap information removal job
    job = GlobalConfig.HIGH_QUEUE.enqueue(__remove_all_info, args=(hostname,), description=f"Delete all info for {hostname}")


def __remove_all_info(hostname):
    """ record the device information after the ping check returns true
       ----------
            hostname:str
               ip address of target device

       """
    index_list = [NMAP_INDEX,VLAN_INDEX,INTERFACE_INDEX]

    total_removed = 0

    for index in index_list:
        elastic_hits = index.query(hostname, field="hostname")

        for eh in elastic_hits['hits']['hits']:

            index.remove_document_by_id(eh['_id'])

        total_removed = total_removed + len(elastic_hits['hits']['hits'])

    LOG_INDEX.generate_log(message=f"{total_removed} namp records for {hostname}",process="remove_all_info")


def __remove_nmap_info(hostname):
    """ record the device information after the ping check returns true
       ----------
            hostname:str
               ip address of target device

       """

    elastic_hits = NMAP_INDEX.query(hostname, field="hostname")

    for eh in elastic_hits['hits']['hits']:

        NMAP_INDEX.remove_document_by_id(eh['_id'])

    total = elastic_hits['hits']['hits']

    LOG_INDEX.generate_log(message=f"{total} namp records for {hostname}",process="remove_namap_info")