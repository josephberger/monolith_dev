import logging

from models import ElasticIndex
from ctrl import Discover


def run(record, appconfig):
    """ run task to add new nmap scan info
   ----------
   record:dict
       record from discover_device_info/retreive_device_info
    envconf: decouple.config
        environmental variables
    """

    discover = Discover(appconfig)

    # elastic configuration
    elastic_host = appconfig.ELASTIC_HOST
    elastic_port = appconfig.ELASTIC_PORT
    nmap_index = appconfig.NMAP_INDEX
    index = ElasticIndex(nmap_index, host=elastic_host, port=elastic_port)

    # get local variables from the record dictionary
    ip = record['ip']
    hostname = record['hostname']

    #get the nmap scan info
    scan_info = discover.nmap_info(ip, hostname)

    #add the new scan information
    index.add_document(scan_info)
    logging.info(f"nmap scanned device {ip}")