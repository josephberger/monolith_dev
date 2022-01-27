import logging
from models import ElasticIndex, PanOSFirewall
import yaml

def record_details(record, appconfig):
    """ record the device information after the ping check returns true
       ----------
        record:dict

        appconfig:config.Config
       """

    device = load(record, appconfig)

    # elastic configs
    elastic_host = appconfig.ELASTIC_HOST
    elastic_port = appconfig.ELASTIC_PORT
    interface_index = appconfig.INTERFACE_INDEX
    gateway_index = appconfig.GATEWAY_INDEX

    try:
        device.retrieve_interfaces()
        device.retrieve_gateways()
    except Exception as e:
        logging.error(f"failed to pull details for {device.hostname} due to {e}")
        return

    index = ElasticIndex(interface_index, host=elastic_host, port=elastic_port)
    for interface in device.interfaces:
        interface['hostname'] = device.hostname
        index.add_document(interface)

    index = ElasticIndex(gateway_index, host=elastic_host, port=elastic_port)
    for gateway in device.gateways:
        gateway['hostname'] = device.hostname
        index.add_document(gateway)

    logging.info(f"details for {device.hostname} pulled")

def load(record, appconfig):

    credentials = appconfig.CREDENTIALS

    with open(credentials, "r") as file:
        credentials = yaml.full_load(file)

    for c in credentials:
        if int(int(record['credential'])) == int(c['id']):
            cred = c
            break

    device = PanOSFirewall(ip=record['ip'], username=cred['username'], password=cred['password'],
                                 hostname=record['hostname'])
    return device
