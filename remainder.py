from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor

from apscheduler.jobstores.mongodb import MongoDBJobStore
from pytz import utc
from pymongo import MongoClient
import secret_settings, telegram
import time
import logging

executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}
jobstores = {
    'mongo': MongoDBJobStore(client=MongoClient(secret_settings.mongo['uri'])),

}

scheduler = BackgroundScheduler(executors=executors, job_defaults=job_defaults, timezone=utc)
scheduler.start()

def add_job(user, time_utc):

    def func():
        telegram.sendMessage(user['chat_id'], "Hey! It is time to learn")

    scheduler.add_job(func, 'interval', days=1, next_run_time = time_utc, id ='%s_1' %(user['chat_id'],) )
    logging.debug(scheduler.get_jobs())

def remove_job(user):
    if scheduler.get_job(job_id='%s_1' %(user['chat_id'],)) is not None :
        scheduler.remove_job(job_id='%s_1' %(user['chat_id'],))



