from config import ElasticConfig
from .queue_data import retrieve_jobs_all
from models import ElasticIndex

#global variables

ENDPOINT_INDEX = ElasticIndex(ElasticConfig.ENDPOINT_INDEX, host=ElasticConfig.HOST, port=ElasticConfig.PORT)
NMAP_INDEX = ElasticIndex(ElasticConfig.NMAP_INDEX, host=ElasticConfig.HOST, port=ElasticConfig.PORT)
VLAN_INDEX = ElasticIndex(ElasticConfig.VLAN_INDEX, host=ElasticConfig.HOST, port=ElasticConfig.PORT)
INTERFACE_INDEX = ElasticIndex(ElasticConfig.INTERFACE_INDEX,
                               host=ElasticConfig.HOST,
                               port=ElasticConfig.PORT)

def reteive_endpoint_info_query(query):


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

def reteive_endpoint_all(hostname):

    info = reteive_endpoint_info(hostname)
    device = {}

    if info:
        device['info'] = info
    else:
        return None

    nmap_info = reteive_nmap_info(hostname)
    if nmap_info:
        device['nmap_info'] = nmap_info

    vlan_info = reteive_vlan_info(hostname)
    if vlan_info:
        device['vlan_info'] = vlan_info

    interface_info = reteive_interface_info(hostname)
    if interface_info:
        device['interface_info'] = interface_info

    return device

def reteive_endpoint_info(hostname):

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

def reteive_interface_info(hostname):

    elastic_hits = INTERFACE_INDEX.query(hostname, field="hostname")

    if elastic_hits['hits']['total']['value'] == 0:
        return None

    interface_info = {}

    for eh in elastic_hits['hits']['hits']:

        if eh["_source"]['hostname'] == hostname.replace('"', ''):

            interface = eh["_source"]
            interface['_id'] = eh['_id']
            interface_name = interface['name']
            del interface['name']
            interface_info[interface_name] = interface

    return interface_info


def reteive_vlan_info(hostname):

    elastic_hits = VLAN_INDEX.query(hostname, field="hostname")

    if elastic_hits['hits']['total']['value'] == 0:
        return None

    vlan_info = {}

    for eh in elastic_hits['hits']['hits']:

        if eh["_source"]['hostname'] == hostname.replace('"', ''):

            vlan = eh["_source"]
            vlan['_id'] = eh['_id']
            vlan_name = vlan['number']
            del vlan['number']
            vlan_info[vlan_name] = vlan


    return vlan_info
