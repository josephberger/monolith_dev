from datetime import datetime
import yaml

from config import GlobalConfig, ElasticConfig, LogConfig
from models import ElasticIndex
from ctrl import discover, load
from models.devices import SwitchCLI

LOG_INDEX = LogConfig.LOG_INDEX

ENDPOINT_INDEX = ElasticIndex(ElasticConfig.ENDPOINT_INDEX,
                              host=ElasticConfig.HOST,
                              port=ElasticConfig.PORT)

EP_DETAILS_INDEX = ElasticIndex(ElasticConfig.EP_DETAILS_INDEX,
                                host=ElasticConfig.HOST,
                                port=ElasticConfig.PORT)
NMAP_INDEX = ElasticIndex(ElasticConfig.NMAP_INDEX,
                          host=ElasticConfig.HOST,
                          port=ElasticConfig.PORT)

VLAN_INDEX = ElasticIndex(ElasticConfig.VLAN_INDEX,
                          host=ElasticConfig.HOST,
                          port=ElasticConfig.PORT)

INTERFACE_INDEX = ElasticIndex(ElasticConfig.INTERFACE_INDEX,
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
            GlobalConfig.HIGH_QUEUE.enqueue(__record_switch_details, args=(record,),
                                            description=f"Record Switch Info {ip}")
        # if record['device_type'] == "linux":
        #     GlobalConfig.HIGH_QUEUE.enqueue(__record_linux_details, args=(record,),
        #                                     description=f"Record Linux Details {ip}")


def __record_nmap_info(record):

    scan_info = discover.discover_nmap_info(record['ip'],record['hostname'])

    NMAP_INDEX.add_document(scan_info)
    LOG_INDEX.generate_log(message=f"nmap scanned device {record['ip']}", process="record_nmap_info")


def __record_switch_details(record):
    """ record the device information after the ping check returns true
       ----------
            record:dict
               record after record device info is run
       """

    switch = load.load_device(record)

    try:
        switch.retrive_config()
        switch.retrieve_vlans()
        switch.parse_interfaces()
    except Exception as e:
        LOG_INDEX.generate_log(message=f"failed to pull infor for {record['hostname']} due to {e}",
                                            process="record_switch_details",
                                            level=3)
        return

    for vlan in switch.vlans:
        vlan['hostname'] = switch.hostname
        VLAN_INDEX.add_document(vlan)

    for interface in switch.interfaces:
        interface['hostname'] = switch.hostname
        INTERFACE_INDEX.add_document(interface)

    LOG_INDEX.generate_log(message=f"Config info for {record['hostname']} pulled", process="record_switch_details")


def __record_linux_details(record):
    """ record the device information after the ping check returns true
       ----------
            record:dict
               record after record device info is run
       """

    details = discover.discover_linux_details(record)

    if details:
        details['hostname'] = record['hostname']
        EP_DETAILS_INDEX.add_document(details)
        LOG_INDEX.generate_log(message=f"Linux details recorded for {record['hostname']}", process="__record_linux_details")
    else:
        LOG_INDEX.generate_log(message=f"Unable to determine linux details recorded for {record['hostname']}",
                               process="__record_linux_details")