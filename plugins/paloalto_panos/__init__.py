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
    zone_index = appconfig.ZONE_INDEX

    # variables extracted from record]
    hostname = record['hostname']
    endpoint_id = record['_id']

    try:
        device.retrieve_interfaces()
        device.retrieve_gateways()
    except Exception as e:
        logging.error(f"failed to pull details for {hostname} due to {e}")
        return

    index = ElasticIndex(interface_index, host=elastic_host, port=elastic_port)
    for interface in device.interfaces:
        interface['hostname'] = hostname
        interface['endpoint_id'] = endpoint_id
        index.add_document(interface)

    index = ElasticIndex(gateway_index, host=elastic_host, port=elastic_port)
    for gateway in device.gateways:
        gateway['hostname'] = hostname
        gateway['endpoint_id'] = endpoint_id
        index.add_document(gateway)

    index = ElasticIndex(zone_index, host=elastic_host, port=elastic_port)
    for zone in device.zones:
        zone['hostname'] = hostname
        zone['endpoint_id'] = endpoint_id
        index.add_document(zone)

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
