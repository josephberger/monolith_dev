from config import ElasticConfig
from .queue_data import retrieve_jobs_all
from models import ElasticIndex

#global variables

ENDPOINT_INDEX = ElasticIndex(ElasticConfig.ENDPOINT_INDEX, host=ElasticConfig.HOST, port=ElasticConfig.PORT)
NMAP_INDEX = ElasticIndex(ElasticConfig.NMAP_INDEX, host=ElasticConfig.HOST, port=ElasticConfig.PORT)

def reteive_device_info_query(query):


    elastic_hits = ENDPOINT_INDEX.lquery(query, exact_match=False)

    if len(elastic_hits['hits']['hits']) > 0:
        hits = []
        for eh in elastic_hits['hits']['hits']:
            hits.append(eh['_source'])

        #TODO determine if the headers and data keys are even needed.  this was a leftover from how the tasks card works
        device_query = {"headers": ["Hostname", "IP Address", "Device Type"],
                        "data_keys": ["hostname", "ip", "device_type"],
                        "data": hits}
        return device_query
    else:
        return None

def reteive_device_all(hostname):
    info = reteive_device_info(hostname)
    device = {}

    if info:
        device['info'] = info
    else:
        return None

    device['nmap_info'] = reteive_nmap_info(hostname)
    return device

def reteive_device_info(hostname):

    elastic_hits = ENDPOINT_INDEX.query(hostname, field="hostname")

    if elastic_hits['hits']['total']['value'] == 0:
        return None

    info = None

    for eh in elastic_hits['hits']['hits']:

        if eh["_source"]['hostname'] == hostname.replace('"', ''):
            info = eh["_source"]
            info['_id'] = eh['_id']
            break

    return info

def reteive_nmap_info(hostname):

    elastic_hits = NMAP_INDEX.query(hostname, field="hostname", sort_field="@timestamp", sort_order="desc")

    if elastic_hits['hits']['total']['value'] == 0:
        return None

    nmap_info = None

    for eh in elastic_hits['hits']['hits']:

        if eh["_source"]['hostname'] == hostname.replace('"', ''):
            nmap_info = eh["_source"]
            nmap_info['_id'] = eh['_id']
            break

    return nmap_info
