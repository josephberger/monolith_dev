from config import Config
from models import ElasticIndex
from config import Config

appconfig = Config

index_list = [appconfig.ENDPOINT_INDEX,
              appconfig.NMAP_INDEX,
              appconfig.VLAN_INDEX,
              appconfig.EP_DETAILS_INDEX,
              appconfig.INTERFACE_INDEX,
              appconfig.GATEWAY_INDEX]

for index_name in index_list:
    index = ElasticIndex(index_name, host=appconfig.ELASTIC_HOST, port=appconfig.ELASTIC_PORT)
    index.delete()
    index.build()