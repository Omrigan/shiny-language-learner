import logging

from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from pymongo import MongoClient
from pytz import utc

import secret_settings
import telegram

executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}

remainders = MongoClient(secret_settings.mongo['uri']).get_default_database().remainders

scheduler = BackgroundScheduler(executors=executors, job_defaults=job_defaults,
                                timezone=utc)
scheduler.start()


def recover_jobs():
    for r in remainders.find():
        def func():
            telegram.send_message(r['chat_id'], "Hey! It is time to learn")

        scheduler.add_job(func, 'interval', days=1, next_run_time=r['time_utc'], id='%s_1' % (r['chat_id'],))


def add_job(user, time_utc):
    def func():
        telegram.send_message(user['chat_id'], "Hey! It is time to learn")

    remainders.save({'chat_id': user['chat_id'],
                     'time_utc': time_utc
                     })
    scheduler.add_job(func, 'interval', days=1, next_run_time=time_utc, id='%s_1' % (user['chat_id'],))
    logging.debug(scheduler.get_jobs())


def remove_job(user):
    if scheduler.get_job(job_id='%s_1' % (user['chat_id'],)) is not None:
        scheduler.remove_job(job_id='%s_1' % (user['chat_id'],))
    remainders.remove({'chat_id': user['chat_id']})
