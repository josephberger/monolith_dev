from config import GlobalConfig

queues = [GlobalConfig.HIGH_QUEUE,GlobalConfig.DEFAULT_QUEUE]

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