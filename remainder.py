from pytz import utc
from pymongo import MongoClient
from . import telegram
import time
import logging
import datetime
import schedule
import time, threading, random

jobs = {}


def get_job(chat_id):
    def send_remainder():
        telegram.send_message(chat_id, "Hey! It is time to learn")
        logging.debug("Added job succeed. Chat id: %s" % (chat_id,))

    jobs[chat_id] = send_remainder
    return jobs[chat_id]


def configure(settings):
    global remainders
    remainders = MongoClient(settings.mongo['uri']).get_default_database().remainders


def to_ugly_time(time):
    return "%s:%s" % (time.hour, time.minute)


def recover_jobs():
    for r in remainders.find():
        r['time_utc'] += datetime.timedelta(days=(datetime.datetime.utcnow() - r['time_utc']).days)
        remainders.save(r)
        jobs[r['chat_id']] = schedule.every().day.at(to_ugly_time(r['time_utc'])).do(get_job(r['chat_id']))


def add_job(user, time_utc):
    jobs[user['chat_id']] = schedule.every().day.at(to_ugly_time(user['time_utc'])).do(get_job(user['chat_id']))
    remainders.save({'chat_id': user['chat_id'],
                     'time_utc': time_utc
                     })


def remove_job(user):
    if user['chat_id'] in jobs:
        schedule.cancel_job(jobs[user['chat_id']])
    remainders.remove({'chat_id': user['chat_id']})


cease_continuous_run = threading.Event()


class ScheduleThread(threading.Thread):
    @classmethod
    def run(cls):
        while not cease_continuous_run.is_set():
            if random.random() < 0.001:
                logging.warning("Random job queue check - total jobs: %s" % len(schedule.default_scheduler.jobs))
            schedule.default_scheduler.run_pending()
            time.sleep(1)


continuous_thread = ScheduleThread()
continuous_thread.start()
