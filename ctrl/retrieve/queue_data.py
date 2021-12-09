from datetime import datetime

def retrieve_jobs_all(queue):

    regs = [queue.started_job_registry,
            queue.finished_job_registry,
            queue.failed_job_registry,
            queue.deferred_job_registry,
            queue.scheduled_job_registry]

    job_ids = queue.get_job_ids()

    for reg in regs:
        job_ids +=reg.get_job_ids()

    job_data = []
    for job_id in job_ids:
        job = queue.fetch_job(job_id)

        job_dict = job.to_dict()
        job_dict['job_id'] = job_id
        job_dict['created_at'] = convert_redis_time(job_dict['created_at'])
        job_dict['enqueued_at'] = convert_redis_time(job_dict['enqueued_at'])
        job_dict['started_at'] = convert_redis_time(job_dict['started_at'])
        job_dict['ended_at'] = convert_redis_time(job_dict['ended_at'])
        job_data.append(job_dict)

    return job_data

def convert_redis_time(redis_time):

    try:
        standard_time = str(datetime.strptime(redis_time,"%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d %H:%M:%S"))
    except:
        standard_time = redis_time

    return standard_time


