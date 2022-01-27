from models import ElasticIndex
from redis import Redis
from rq import Queue
from datetime import datetime

class Retrieve:
    def __init__(self, appconfig):
        self.elastic_host = appconfig.ELASTIC_HOST
        self.elastic_port = appconfig.ELASTIC_PORT
        self.endpoint_index = appconfig.ENDPOINT_INDEX
        self.nmap_index = appconfig.NMAP_INDEX
        self.interface_index = appconfig.INTERFACE_INDEX
        self.vlan_index = appconfig.VLAN_INDEX
        self.gateway_index = appconfig.GATEWAY_INDEX
        self.redis_host = appconfig.REDIS_HOST
        self.redis_port = appconfig.REDIS_PORT
    def endpoint_info_query(self, query):

        index = ElasticIndex(self.endpoint_index, host=self.elastic_host, port=self.elastic_port)
        elastic_hits = index.lquery(query, exact_match=False)

        if len(elastic_hits['hits']['hits']) > 0:
            hits = []
            for eh in elastic_hits['hits']['hits']:
                hits.append(eh['_source'])

            # TODO determine if the headers and data keys are even needed.  this was a leftover from how the tasks card works
            device_query = {"headers": ["Hostname", "IP Address", "Device Type"],
                            "data_keys": ["hostname", "ip", "device_type"],
                            "data": hits}
            return device_query
        else:
            return None

    def endpoint_all(self, hostname):

        info = self.endpoint_info(hostname)
        device = {}

        if info:
            device['info'] = info
        else:
            return None

        nmap_info = self.nmap_info(hostname)
        if nmap_info:
            device['nmap_info'] = nmap_info

        vlan_info = self.vlan_info(hostname)
        if vlan_info:
            device['vlan_info'] = vlan_info

        interface_info = self.interface_info(hostname)
        if interface_info:
            device['interface_info'] = interface_info

        gateway_info = self.gateway_info(hostname)
        if gateway_info:
            device['gateway_info'] = gateway_info

        return device

    def endpoint_info(self,hostname):

        index = ElasticIndex(self.endpoint_index, host=self.elastic_host, port=self.elastic_port)
        elastic_hits = index.lquery(hostname, field="hostname")

        if elastic_hits['hits']['total']['value'] == 0:
            return None

        info = None

        for eh in elastic_hits['hits']['hits']:

            if eh["_source"]['hostname'] == hostname.replace('"', ''):
                info = eh["_source"]
                info['_id'] = eh['_id']
                break

        return info

    def nmap_info(self, hostname):

        index = ElasticIndex(self.nmap_index, host=self.elastic_host, port=self.elastic_port)

        try:
            elastic_hits = index.query(hostname, field="hostname", sort_field="@timestamp", sort_order="desc")
        except:
            return None

        if elastic_hits['hits']['total']['value'] == 0:
            return None

        nmap_info = None

        for eh in elastic_hits['hits']['hits']:

            if eh["_source"]['hostname'] == hostname.replace('"', ''):
                nmap_info = eh["_source"]
                nmap_info['_id'] = eh['_id']
                break

        return nmap_info


    def interface_info(self, hostname):
        index = ElasticIndex(self.interface_index, host=self.elastic_host, port=self.elastic_port)
        elastic_hits = index.query(hostname, field="hostname")

        if elastic_hits['hits']['total']['value'] == 0:
            return None

        interface_info = {}

        for eh in elastic_hits['hits']['hits']:

            try:
                if eh["_source"]['hostname'] == hostname.replace('"', ''):
                    interface = eh["_source"]
                    interface['_id'] = eh['_id']
                    interface_name = interface['name']
                    del interface['name']
                    interface_info[interface_name] = interface
            except:
                return None

        return interface_info


    def vlan_info(self, hostname):
        index = ElasticIndex(self.vlan_index, host=self.elastic_host, port=self.elastic_port)
        elastic_hits = index.query(hostname, field="hostname")

        if elastic_hits['hits']['total']['value'] == 0:
            return None

        vlan_info = {}

        for eh in elastic_hits['hits']['hits']:

            if eh["_source"]['hostname'] == hostname.replace('"', ''):
                vlan = eh["_source"]
                vlan['_id'] = eh['_id']
                vlan_name = vlan['number']
                del vlan['number']
                vlan_info[vlan_name] = vlan

        return vlan_info

    def gateway_info(self, hostname):
        index = ElasticIndex(self.gateway_index, host=self.elastic_host, port=self.elastic_port)
        elastic_hits = index.query(hostname, field="hostname")

        if elastic_hits['hits']['total']['value'] == 0:
            return None

        gw_info = {}

        for eh in elastic_hits['hits']['hits']:

            if eh["_source"]['hostname'] == hostname.replace('"', ''):
                gw = eh["_source"]
                gw['_id'] = eh['_id']
                name = gw['gateway-name']
                del gw['gateway-name']
                gw_info[name] = gw

        return gw_info

    def jobs_all(self, queue_name):

        redis_connection = Redis(host=self.redis_host, port=self.redis_port, db=0)
        queue = Queue(connection=redis_connection, name=queue_name)

        regs = [queue.started_job_registry,
                queue.finished_job_registry,
                queue.failed_job_registry,
                queue.deferred_job_registry,
                queue.scheduled_job_registry]

        job_ids = queue.get_job_ids()

        for reg in regs:
            job_ids += reg.get_job_ids()

        job_data = []
        for job_id in job_ids:
            job = queue.fetch_job(job_id)

            job_dict = job.to_dict()
            job_dict['job_id'] = job_id
            job_dict['created_at'] = self.convert_redis_time(job_dict['created_at'])
            job_dict['enqueued_at'] = self.convert_redis_time(job_dict['enqueued_at'])
            job_dict['started_at'] = self.convert_redis_time(job_dict['started_at'])
            job_dict['ended_at'] = self.convert_redis_time(job_dict['ended_at'])
            job_data.append(job_dict)

        return job_data

    def convert_redis_time(self, redis_time):

        try:
            standard_time = str(datetime.strptime(redis_time, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d %H:%M:%S"))
        except:
            standard_time = redis_time

        return standard_time