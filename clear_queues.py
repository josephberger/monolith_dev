from config import Config
from rq import Queue
from redis import Redis
appconfig = Config()

redis_host = appconfig.REDIS_HOST
redis_port = appconfig.REDIS_PORT
redis_connection = Redis(host=redis_host, port=redis_port, db=0)
high_queue = Queue(connection=redis_connection, name="high")
default_queue = Queue(connection=redis_connection, name="default")

queues = [high_queue,default_queue]

for q in queues:
    q.empty()

    regs = [q.started_job_registry,
            q.finished_job_registry,
            q.failed_job_registry,
            q.deferred_job_registry,
            q.scheduled_job_registry]

    for reg in regs:
        for job_id in reg.get_job_ids():
            reg.remove(job_id, delete_job=True)