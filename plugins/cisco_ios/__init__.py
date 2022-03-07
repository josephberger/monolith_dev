#
# Joseph Berger <airmanberger@gmail.com>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

import logging
from models import ElasticIndex
from models import SwitchCLI
import yaml
import re

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
        vlan['endpoint_id'] = record['_id']
        index.add_document(vlan)

    # set interface index and record
    index = ElasticIndex(interface_index, host=elastic_host, port=elastic_port)
    for interface in device.interfaces:
        interface['hostname'] = device.hostname
        interface['endpoint_id'] = record['_id']
        index.add_document(interface)

    # get the endpoint system details
    version = device.cli.send_command("show version")
    endpoint_details = {}
    matches = re.findall(r"(.+?)(\s+?:|\:\s+)(.+?)\n", version)
    for m in matches:
        if len(m) == 3:
            key = m[0].lstrip().rstrip().lower().replace(" ", "_")
            value = m[2].lstrip().rstrip().lower().replace(" ", "_")
            endpoint_details[key] = value
    endpoint_details['hostname'] = device.hostname
    endpoint_details['endpoint_id'] = record['_id']
    index = ElasticIndex('ep_details', elastic_host, elastic_port)
    index.add_document(endpoint_details)

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
    endpoint_id = record['_id']

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
        interface['hostname'] = hostname
        interface['endpoint_id'] = endpoint_id
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
    endpoint_id = record['_id']

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
        vlan['endpoint_id'] = endpoint_id
        vlan['hostname'] = hostname
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
