from config import GlobalConfig, LogConfig

from ctrl import discover
from config import ElasticConfig
from models import ElasticIndex

NMAP_INDEX = ElasticIndex(ElasticConfig.NMAP_INDEX,
                          host=ElasticConfig.HOST,
                          port=ElasticConfig.PORT)

LOG_INDEX = LogConfig.LOG_INDEX

def run(record):
    """ run task that will update device information ping->update
       ----------
           record:dict
               record from discover_device_info/retreive_device_info
    """

    scan_info = discover.discover_nmap_info(record['ip'], record['hostname'])

    NMAP_INDEX.add_document(scan_info)
    LOG_INDEX.generate_log(message=f"nmap scanned device {record['ip']}", process="record_nmap_info")