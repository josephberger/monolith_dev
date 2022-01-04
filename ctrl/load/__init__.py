import netmiko

from config import GlobalConfig
import yaml
from models.devices import SwitchCLI
CREDENTIALS = GlobalConfig.CREDENTIALS

def load_device(record):
    """ load the device and return
       ----------
            record:dict
               record after record device info is run
       """

    if record['device_type'] == "cisco_ios":

        cred = load_credential(record['credential'])

        device_info = {
            'device_type': record['device_type'],
            'ip': record['ip'],
            'username': cred['username'],
            'password': cred['password'],
            'secret': cred['secret'],
            'hostname': record['hostname'],
        }

        switch = SwitchCLI(**device_info)

        return switch

    if record['device_type'] == "linux":

        cred = load_credential(record['credential'])

        device_info = {
            'device_type': record['device_type'],
            'ip': record['ip'],
            'username': cred['username'],
            'password': cred['password'],
            'port': 22,
        }

        linux = netmiko.ConnectHandler(**device_info)

        return linux

    else:

        return None


def load_credential(id):
    """ credential loader for all device types
       ----------
            id:int
               id of the credentials
       """

    with open(CREDENTIALS, "r") as file:
        credentials = yaml.full_load(file)

    for c in credentials:
        if int(int(id)) == int(c['id']):
            return c