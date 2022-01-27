import logging
from models import ElasticIndex
from models import SwitchCLI
import yaml

def record_details(record, appconfig):
    """ record the device information after the ping check returns true
       ----------
        device:dict

        appconfig:config.Config
       """
    device = load(record, appconfig)

    # elastic configs
    elastic_host = appconfig.ELASTIC_HOST
    elastic_port = appconfig.ELASTIC_PORT
    vlan_index = appconfig.VLAN_INDEX
    interface_index = appconfig.INTERFACE_INDEX

    # try to pull configuration
    try:
        device.retrive_config()
        device.retrieve_vlans()
        device.parse_interfaces()
    except Exception as e:
        logging.error(f"failed to pull details for {device.hostname} due to {e}")
        return

    # set vlan index and record
    index = ElasticIndex(vlan_index, host=elastic_host, port=elastic_port)
    for vlan in device.vlans:
        vlan['hostname'] = device.hostname
        index.add_document(vlan)

    # set interface index and record
    index = ElasticIndex(interface_index, host=elastic_host, port=elastic_port)
    for interface in device.interfaces:
        interface['hostname'] = device.hostname
        index.add_document(interface)

    logging.info(f"details for {device.hostname} pulled")


def rediscover_interface_info(record, appconfig):
    """ record the device information after the ping check returns true
       ----------
            record:dict
               record from discover_device_info
            appconfig: config.Config
                environmental variables

        """

    #load the device
    device = load(record, appconfig)

    # elastic configs
    elastic_host = appconfig.ELASTIC_HOST
    elastic_port = appconfig.ELASTIC_PORT
    interface_index = appconfig.INTERFACE_INDEX

    # variables extracted from record]
    hostname = record['hostname']

    # if interfaces pulled successfully, continue
    try:
        device.retrieve_interfaces()
    except Exception as e:
        logging.error(f"failed to pull interfaces for {record['hostname']} due to {e}")
        return

    #set the index
    index = ElasticIndex(interface_index, elastic_host, elastic_port)

    # remove the existing records from vlan index
    elastic_hits = index.query(hostname, field="hostname")

    for eh in elastic_hits['hits']['hits']:
        index.remove_document_by_id(eh['_id'])

    # set interface index and record
    for interface in device.interfaces:
        interface['hostname'] = device.hostname
        index.add_document(interface)

    logging.info(f"updated interfaces for endpoint {hostname}")


def rediscover_vlan_info(record, appconfig):
    """ record the device information after the ping check returns true
       ----------
            record:dict
               record from discover_device_info
            envconf: decouple.config
                environmental variables

        """

    # load the device
    device = load(record, appconfig)

    # elastic configs
    elastic_host = appconfig.ELASTIC_HOST
    elastic_port = appconfig.ELASTIC_PORT
    vlan_index = appconfig.INTERFACE_INDEX

    #variables extracted from record]
    hostname = record['hostname']

    # if vlans pulled successfully, continue
    try:
        device.retrieve_vlans()
    except Exception as e:
        logging.error(f"failed to pull interfaces for {record['hostname']} due to {e}")
        return

    # set the index
    index = ElasticIndex(vlan_index, elastic_host, elastic_port)

    #remove the existing records from vlan index
    elastic_hits = index.query(hostname, field="hostname")

    for eh in elastic_hits['hits']['hits']:
        index.remove_document_by_id(eh['_id'])

    # set vlan index and record
    for vlan in device.vlans:
        vlan['hostname'] = device.hostname
        index.add_document(vlan)

    logging.info(f"updated vlans for endpoint {hostname}")


def load(record, appconfig):
    """  load the device and return appopriate object
       ----------
            record:dict
               record from discover_device_info
            appconfig: config.Config
                environmental variables

        """
    credentials = appconfig.CREDENTIALS

    with open(credentials, "r") as file:
        credentials = yaml.full_load(file)

    for c in credentials:
        if int(int(record['credential'])) == int(c['id']):
            cred = c
            break

    device_info = {
        'device_type': record['device_type'],
        'ip': record['ip'],
        'username': cred['username'],
        'password': cred['password'],
        'secret': cred['secret'],
        'hostname': record['hostname'],
    }

    device = SwitchCLI(**device_info)

    return device
