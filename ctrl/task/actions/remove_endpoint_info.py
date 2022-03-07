import logging

from models import ElasticIndex

def run(record, appconfig):
    """ run task that removes all the information associated with an endpoint
   ----------
   record:dict
       record from discover_device_info/retreive_device_info
   appconfig: config.Config
        environmental variables
   """

    # elastic configuration
    elastic_host = appconfig.ELASTIC_HOST
    elastic_port = appconfig.ELASTIC_PORT
    endpoint_index = appconfig.ENDPOINT_INDEX
    nmap_index = appconfig.NMAP_INDEX
    vlan_index = appconfig.VLAN_INDEX
    interface_index = appconfig.INTERFACE_INDEX
    gateway_index = appconfig.GATEWAY_INDEX
    zone_index = appconfig.ZONE_INDEX

    #get local variables from the record dictionary
    hostname = record['hostname']
    record_id = record['_id']

    #remove the endpoint info from the endpoint index
    index = ElasticIndex(endpoint_index, host=elastic_host, port=elastic_port)
    index.remove_document_by_id(doc_id=record_id)
    logging.info(f"deleted {hostname} endpoint information")

    #create index list for enumaration
    index_list = [nmap_index,vlan_index,interface_index,gateway_index, zone_index]

    total_removed = 0

    #for each index name in the index_list, delete all records pertaining to hostname and increase total_removed by 1
    for index_name in index_list:
        index = ElasticIndex(index_name, host=elastic_host, port=elastic_port)
        elastic_hits = index.query(hostname, field="hostname")

        for eh in elastic_hits['hits']['hits']:

            index.remove_document_by_id(eh['_id'])

        total_removed = total_removed + len(elastic_hits['hits']['hits'])

    logging.info(f"{total_removed} records for {hostname}")