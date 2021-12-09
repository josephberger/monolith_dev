from datetime import datetime
import yaml

from config import GlobalConfig, ElasticConfig, LogConfig
from models import ElasticIndex
from ctrl import discover
from models.devices import SwitchCLI

LOG_INDEX = LogConfig.LOG_INDEX

ENDPOINT_INDEX = ElasticIndex(ElasticConfig.ENDPOINT_INDEX,
                              host=ElasticConfig.HOST,
                              port=ElasticConfig.PORT)
NMAP_INDEX = ElasticIndex(ElasticConfig.ENDPOINT_INDEX,
                          host=ElasticConfig.HOST,
                          port=ElasticConfig.PORT)

VLAN_INDEX = ElasticIndex(ElasticConfig.VLAN_INDEX,
                          host=ElasticConfig.HOST,
                          port=ElasticConfig.PORT)

def run(ip):
    """ initial run method for the entire task
       ----------
           ip:str
               ip address of target device
       """
    result = discover.discover_ping_check(ip)
    if result:
        job = GlobalConfig.HIGH_QUEUE.enqueue(__record_device_info, args=(ip,), description=f"Record Device Info {ip}")
        LOG_INDEX.generate_log(message=f"ping response from {ip} - Starting job {job.id}")
    else:
        LOG_INDEX.generate_log(message=f"no ping response from {ip}")


def __record_device_info(ip):
    """ record the device information after the ping check returns true
       ----------
            ip:str
               ip address of target device
            credentials_file: str
                path to credentials file
            logger: models.ESLogger
                elasticsearch logger index

       """

    record = discover.discover_device_info(ip, GlobalConfig.CREDENTIALS)
    record['update_time'] = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    #record device in elasticsearch device index
    ENDPOINT_INDEX.add_document(record)

    #add the nmap scan to the high queue
    GlobalConfig.HIGH_QUEUE.enqueue(__record_nmap_info, args=(record,), description=f"Record NMAP Info {ip}")

    if record['device_type'] == "unknown":
        LOG_INDEX.generate_log(message=f"unable to determine credentials and device_type for {ip}",process="record_device_info")
        return
    else:
        LOG_INDEX.generate_log(message=f"device_type for {ip} discovered: {record['device_type']}", process="record_device_info")

        if record['device_type'] == "cisco_ios":
            GlobalConfig.HIGH_QUEUE.enqueue(__record_switch_info, args=(record,), description=f"Record Switch Info {ip}")

def __record_nmap_info(record):

    scan_info = discover.discover_nmap_info(record['ip'],record['hostname'])

    NMAP_INDEX.add_document(scan_info)
    LOG_INDEX.generate_log(message=f"nmap scanned device {record['ip']}", process="record_nmap_info")

def __record_switch_info(record):
    """ record the device information after the ping check returns true
       ----------
            record:dict
               record after record device info is run
            credentials_file: str
                path to credentials file
            logger: models.ESLogger
                elasticsearch logger index
       """
    credential = load_credential(record['credential'], GlobalConfig.CREDENTIALS)

    device_info = {
        'device_type': record['device_type'],
        'ip': record['ip'],
        'username': credential['username'],
        'password': credential['password'],
        'secret': credential['secret'],
        'hostname': record['hostname'],
    }

    try:
        switch = SwitchCLI(**device_info)
        switch.retrieve_vlans()
    except Exception as e:
        LOG_INDEX.generate_log(message=f"failed to pull infor for {record['hostname']} due to {e}",
                                            process="record_switch_info",
                                            level=3)
        return

    for vlan in switch.vlans:
        vlan['hostname'] = switch.hostname
        VLAN_INDEX.add_document(vlan)

    LOG_INDEX.generate_log(message=f"config info for {record['hostname']} pulled", process="record_switch_info")

def load_credential(id, credentials_file):
    """ credential loader for all device types
       ----------
            id:int
               id of the credentials
            credentials_file: str
                path to credentials file
       """

    with open(credentials_file, "r") as file:
        credentials = yaml.full_load(file)

    for c in credentials:
        if int(int(id)) == int(c['id']):
            return c