import datetime
import logging
import os
import re
import time
import traceback

import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from nltk.stem.wordnet import WordNetLemmatizer

from . import my_correction
from . import study_settings
from . import telegram
from . import train, remainder

env = os.getenv('BOT_ENV', 'staging')


class States:
    idle = 1
    langs_asked = 2


class App:
    def __init__(self, settings):
        dirname = os.path.dirname(os.path.realpath(__file__)) + '/'
        self.logger = logging.getLogger("bot")
        self.help_text = open(dirname + 'docs/help.txt').read()
        self.changelog_text = open(dirname + 'docs/changelog.txt').read()
        self.settings = settings
        self.wnl = WordNetLemmatizer()
        remainder.configure(settings)

        ###LOGGING
        access = logging.FileHandler('access.log')
        access.setLevel(logging.INFO)
        access.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

        error = logging.FileHandler('error.log')
        error.setLevel(logging.ERROR)
        error.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(access)
        self.logger.addHandler(error)
        if env == 'debug':
            logging.basicConfig(level=logging.DEBUG)
        logging.warning("Cofiguration: %s" % (env,))

        self.db = MongoClient(settings.mongo['uri']).get_default_database()
        if 'users' not in self.db.collection_names():
            self.db.create_collection('users')
        self.users = self.db.users
        if 'remainders' not in self.db.collection_names():
            self.db.create_collection('remainders')
        remainder.recover_jobs()

        self.params['offset'] = 0
        logging.warning('Constructed')

    def listen(self):
        logging.warning('Listening')
        while True:
            self.get_updates()
            time.sleep(0.1)

            # app.run()

    def correct(self, string):
        baseurl_correction = 'http://service.afterthedeadline.com/checkDocument'
        correction = requests.get(baseurl_correction, {'data': string}).text
        correction = BeautifulSoup(correction, "lxml")

        if correction.find("option") is not None:
            string = correction.find("option").string
        return string

    def add_word(self, user, string):

        baseurl = 'https://translate.yandex.net/api/v1.5/tr.json/translate'
        # string = re.sub(r'[^A-Za-z\s]', '', string)
        # string = re.sub(r'\Wk+', ' ', string)
        string = string.lower()

        if len(string) == 0:
            telegram.send_message(user['chat_id'], "Wrong word")
            return

        # string = correct(string)
        if user['foreign'] == 'en':
            string = my_correction.correct(string)
            if env != 'debug':
                string = self.wnl.lemmatize(string)
        string = string[0].upper() + string[1:]
        if 'direction' not in user:
            user['foreign'] = 'en'
            user['native'] = 'ru'
        direction = '%s-%s' % (user['foreign'], user['native'])
        transtaltion = requests.get(baseurl, {
            'key': self.settings.translate_yandex['token'],
            'lang': direction,
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
            self.users.save(user)
            telegram.send_message(user['chat_id'], "Word added\n%s - %s" % (string, out_word))
        else:
            telegram.send_message(user['chat_id'], "Already exist!\n%s - %s" % (string, out_word))

    params = {}

    def get_list_word(self, user, text):
        str_out = "\n".join(["%s: (%s) %s - %s" % (i + 1, w['stage'], w['en'], w['ru']) for i, w in
                             zip(range(10 ** 10), user['words'])])
        telegram.send_message(user['chat_id'], str_out)

    def start(self, user, text):
        telegram.send_message(user['chat_id'], """
Welcome!
I am a bot.
To learn how to use me, print /help.
Now you have to choose you foreign and native language.
Example: en-ru (en is foreign and ru is native)
To get list of language codes write help
        """)
        user['state'] = States.langs_asked

    def langs_ask(self, user, text):
        ans = requests.get('https://translate.yandex.net/api/v1.5/tr.json/getLangs',
                           {'key': self.settings.translate_yandex['token']})
        lang_list = ans.json()['dirs']
        if text not in lang_list:
            telegram.send_message(user['chat_id'], "Please, choose any of this:\n" + "\n".join(lang_list))
        else:
            telegram.send_message(user['chat_id'], "\"%s\" have successfully chosen" % (text,))
            user['state'] = States.idle

            user['foreign'] = text[0:2]
            user['native'] = text[3:5]

    def help(self, user, text):
        telegram.send_message(user['chat_id'], self.help_text)

    def start_train(self, user, text):
        user['train']['type'] = 0
        train.do_train(user, text)

    def add_remainder(self, user, text):
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

    def remove_remainder(self, user, text):
        remainder.remove_job(user)
        telegram.send_message(user['chat_id'], "Removed")

    def remove(self, user, text):
        if user['train']['type'] != 0:
            for w in user['words']:
                if w == user['train']['word']:
                    user['words'].remove(w)
                    str_out = "%s - %s" % (w['en'], w['ru'])
                    telegram.send_message(user['chat_id'], "Deleted:\n%s" % (str_out,))

            train.do_train(user, text)


        else:
            tokens = text.split(" ")
            if len(tokens) > 1:
                cnt = int(tokens[1]) - 1
            else:
                cnt = -1
            str_out = "%s - %s" % (user['words'][cnt]['en'], user['words'][cnt]['ru'])
            del user['words'][cnt]
            telegram.send_message(user['chat_id'], "Word with index %s removed\n%s" % (cnt, str_out))

    comands = {
        'list': get_list_word,
        'rm': remove,
        'train': start_train,
        'end': train.end_train,
        'start': start,
        'help': help,
        'setremainder': add_remainder,
        'removeremainder': remove_remainder
    }

    def parse_action(self, chat_id, text):
        self.logger.warning("%s - %s" % (chat_id, text))
        user = self.users.find_one({'chat_id': chat_id})
        if user is None:
            user = {'chat_id': chat_id,
                    'state': States.idle,

                    'words': [],
                    'train': {
                        'type': 0,
                        'words': 0,
                        'correct': 0,
                        'cadidacies': []
                    }}
        if 'train' not in user:
            user['train'] = {
                'type': 0,
                'words': 0,
                'correct': 0,
                'cadidacies': []
            }
        if text[0] == '/':  # Command
            cmd = text[1:].lower().split(' ')[0]
            if cmd in self.comands:
                self.comands[cmd](self, user, text)
        elif user['train']['type'] != 0:
            train.do_train(user, text)
        elif user['state'] == States.idle:
            self.add_word(user, text)
        elif user['state'] == States.langs_asked:
            self.langs_ask(user, text)
        self.users.save(user)

    def get_updates(self):
        messages = telegram.get_updates(self.params['offset'])
        for u in messages:
            if 'message' in u:
                if u['update_id'] < self.params['offset']:
                    print('Error')
                else:
                    chat_id = u['message']['chat']['id']
                    text = u['message']['text']
                    self.params['offset'] = max(self.params['offset'], u['update_id'] + 1)
                    try:
                        self.parse_action(chat_id, text)
                    except:
                        logging.error('Error! (%s, %s)' % (chat_id, text))
                        logging.error(traceback.print_exc())
                        telegram.send_message(chat_id, 'An error occurred!')

        self.db.meta.save(self.params)
