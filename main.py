import datetime
import logging
import os
import re
import time
import traceback

import requests
from bs4 import BeautifulSoup
from nltk.stem import WordNetLemmatizer
from pymongo import MongoClient

import remainder
import secret_settings
import study_settings
import telegram
import train

env = os.getenv('BOT_ENV', 'staging')


class States:
    idle = 1
    translates_proposed = 2


logger = logging.getLogger("bot")
help_text = open('docs/help.txt').read()
changelog_text = open('docs/changelog.txt').read()
wnl = WordNetLemmatizer()


def correct(string):
    base_url_correction = 'http://service.afterthedeadline.com/checkDocument'
    correction = requests.get(base_url_correction, {'data': string}).text
    correction = BeautifulSoup(correction, "lxml")

    if correction.find("option") is not None:
        string = correction.find("option").string
    return string


def add_word(user, string):
    base_url = 'https://translate.yandex.net/api/v1.5/tr.json/translate'
    string = re.sub(r'[^A-Za-z\s]', '', string)
    string = re.sub(r'\Wk+', ' ', string)
    string = string.lower()

    if len(string) == 0:
        telegram.send_message(user['chat_id'], "Wrong word")
        return

    string = correct(string)
    # string =my_correction.correct(string)
    t = time.time()
    if env != 'debug':
        string = wnl.lemmatize(string)
    print(time.time() - t, ' secs')
    string = string[0].upper() + string[1:]
    transtaltion = requests.get(base_url, {
        'key': secret_settings.translate_yandex['token'],
        'lang': 'ru',
        'text': string
    })
    out_word = transtaltion.json()['text'][0]

    already_has = False
    for w in user['words']:
        already_has |= w["en"] == string
    if not already_has:
        user['words'].append({"en": string, "ru": out_word,
                              "stage": study_settings.min_stage,
                              "expiration_date": datetime.datetime.utcnow() + study_settings.stages[1],
                              "creation_date": datetime.datetime.utcnow()})
        users.save(user)
        telegram.send_message(user['chat_id'], "Word added\n%s - %s" % (string, out_word))
    else:
        telegram.send_message(user['chat_id'], "Already exist!\n%s - %s" % (string, out_word))


params = {}


def erase_last_word(user, text):
    if len(user['words']) > 0:
        str_out = "%s - %s" % (user['words'][-1]['en'], user['words'][-1]['ru'])
        user['words'] = user['words'][:-1]
        telegram.send_message(user['chat_id'], "Last word erased\n" + str_out)


def get_list_word(user, text):
    str_out = "\n".join(["(%s) %s - %s" % (w['stage'], w['en'], w['ru']) for w in user['words']])
    telegram.send_message(user['chat_id'], str_out)


def start(user, text):
    telegram.send_message(user['chat_id'], """
    Welcome
    I am an EnglishWordRepeater bot.
    To learn how to use me, print /help
    """)


def send_help(user, text):
    telegram.send_message(user['chat_id'], help_text)


def start_train(user, text):
    user['train']['type'] = 0
    train.do_train(user, text)


def add_remainder(user, text):
    remainder.remove_job(user)
    tokens = text.split(' ')
    delta = datetime.timedelta()
    if len(tokens) >= 2:
        tokens = tokens[1].replace(' ', '').split(':')
        hours = int(tokens[0])
        minutes = int(tokens[1])
        delta = datetime.timedelta(hours=hours, minutes=minutes)
    remainder.add_job(user, datetime.datetime.utcnow() + delta)
    telegram.send_message(user['chat_id'], "Successfully set. Nearest at  %s" % (datetime.datetime.now() + delta,))


def remove_remainder(user, text):
    remainder.remove_job(user)
    telegram.send_message(user['chat_id'], "Removed")


comands = {
    'eraselast': erase_last_word,
    'getlist': get_list_word,
    'starttrain': start_train,
    'endtrain': train.end_train,
    'start': start,
    'help': send_help,
    'setremainder': add_remainder,
    'removeremainder': remove_remainder
}


def parse_action(chat_id, text):
    logger.warning("%s - %s" % (chat_id, text))
    user = users.find_one({'chat_id': chat_id})
    if user is None:
        user = {'chat_id': chat_id,
                'state': States.idle,

                'words': [],
                'train': {
                    'type': 0,
                    'words': 0,
                    'correct': 0,
                    'candidacies': []
                }}
    if 'train' not in user:
        user['train'] = {
            'type': 0,
            'words': 0,
            'correct': 0,
            'candidacies': []
        }
    if text[0] == '/':  # Command
        cmd = text[1:].lower().split(' ')[0]
        if cmd in comands:
            comands[cmd](user, text)
    else:
        if user['train']['type'] != 0:
            train.do_train(user, text)
        elif user['state'] == States.idle:
            add_word(user, text)
    users.save(user)


def get_updates():
    messages = telegram.get_updates(params['offset'])
    for u in messages:
        if 'message' in u:
            if u['update_id'] < params['offset']:
                print('Error')
            else:
                chat_id = u['message']['chat']['id']
                text = u['message']['text']
                params['offset'] = max(params['offset'], u['update_id'] + 1)
                try:
                    parse_action(chat_id, text)
                except:
                    logging.error('Error! (%s, %s)' % (chat_id, text))
                    logging.error(traceback.print_exc())
                    telegram.send_message(chat_id, 'Parse error! Try again')

    db.meta.save(params)


if __name__ == "__main__":

    #  LOGGING
    access = logging.FileHandler('access.log')
    access.setLevel(logging.INFO)
    access.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    error = logging.FileHandler('error.log')
    error.setLevel(logging.ERROR)
    error.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(access)
    logger.addHandler(error)
    if env == 'debug':
        logging.basicConfig(level=logging.DEBUG)
    logging.warning("Cofiguration: %s" % (env,))

    db = MongoClient(secret_settings.mongo['uri']).get_default_database()
    if 'users' not in db.collection_names():
        db.create_collection('users')
    users = db.users
    if 'remainders' not in db.collection_names():
        db.create_collection('remainders')
    remainder.recover_jobs()

    params['offset'] = 0
    logging.warning('Started')
    while True:
        get_updates()
        time.sleep(0.1)
        # app.run()
