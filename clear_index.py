from config import ElasticConfig
from models import ElasticIndex

index_list = [ElasticConfig.ENDPOINT_INDEX,
              ElasticConfig.NMAP_INDEX,
              ElasticConfig.VLAN_INDEX,
              ElasticConfig.EP_DETAILS_INDEX,
              ElasticConfig.INTERFACE_INDEX]

for index_name in index_list:
    index = ElasticIndex(index_name, host=ElasticConfig.HOST, port=ElasticConfig.PORT)
    index.delete()
    index.build()