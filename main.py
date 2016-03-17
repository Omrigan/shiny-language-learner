from flask import Flask
from pymongo import MongoClient
import secret_settings, study_settings
import telegram
from nltk.stem import WordNetLemmatizer

from train import startTrain, endTrain
import random, re
from enum import Enum

import time, datetime
import logging, argparse
from xml.etree import ElementTree
from bs4 import BeautifulSoup
import requests
app = Flask(__name__)


class States():
    idle = 1
    translates_proposed = 2



logger = logging.getLogger("bot")
help_text = open('docs/help.txt').read()
changelog_text = open('docs/changelog.txt').read()
wnl = WordNetLemmatizer()
def addWord(user, string):
    baseurl = 'https://translate.yandex.net/api/v1.5/tr.json/translate'
    #correct = requests.get('http://suggestqueries.google.com/complete/search?client=firefox&q=%s' %(string)).json()

    string = re.sub(r'[^A-Za-z\s]', '', string)
    string = re.sub(r'\Wk+', ' ', string)
    string = string.lower()
    #string = wnl.lemmatize(string)
    if len(string) == 0:
        telegram.sendMessage(user['chat_id'], "Wrong word")
        return;
    string = string[0].upper() + string[1:]

    baseurl_correction = 'http://service.afterthedeadline.com/checkDocument'
    correction = requests.get(baseurl_correction, {'data': string}).text
    correction = BeautifulSoup(correction)


    if correction.find("option") is not None:
        string = correction.find("option").string


    transtaltion = requests.get(baseurl, {
        'key': secret_settings.translate_yandex['token'],
        'lang': 'ru',
        'text': string
    })
    out_word = transtaltion.json()['text'][0]


    already_has = False
    for w in user['words']:
        already_has |= w["en"]==string
    if not already_has:
        user['words'].append({"en": string, "ru": out_word,
                              "stage": study_settings.min_stage,
                              "expiration_date": datetime.datetime.utcnow() + study_settings.stages[1],
                              "creation_date": datetime.datetime.utcnow()})
        users.save(user)
        telegram.sendMessage(user['chat_id'], "Word added\n%s - %s" % (string, out_word))
    else:
        telegram.sendMessage(user['chat_id'], "Already exist!\n%s - %s" % (string, out_word))

params = {}

def eraseLastWord(user, text):
    if(len(user['words'])>0):
        str_out = "%s - %s" % (user['words'][-1]['en'], user['words'][-1]['ru'])
        user['words'] = user['words'][:-1]
        telegram.sendMessage(user['chat_id'], "Last word erased\n" + str_out)

def getListWord(user, text):
    str_out = "\n".join(["(%s) %s - %s" % (w['stage'], w['en'], w['ru']) for w in user['words']])
    telegram.sendMessage(user['chat_id'], str_out)

def start(user, text):
    telegram.sendMessage(user['chat_id'], """
    Welcome
    I am an EnglishWordRepeater bot.
    To learn how to use me, print /help
    """)
def help(user, text):
    telegram.sendMessage(user['chat_id'], help_text)



comands = {
    'eraselast': eraseLastWord,
    'getlist': getListWord,
    'starttrain': startTrain,
    'endtrain': endTrain,
    'start': start,
    'help': help
}

def parseAction(chat_id, text):
    logger.warning("%s - %s" %(chat_id, text))
    user = users.find_one({'chat_id': chat_id})
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
    if text[0]=='/': #Command
        cmd = text[1:].lower()
        if cmd in comands:
            comands[cmd](user, text)
    else:
        if user['train']['type']!=0:
            startTrain(user, text)
        elif user['state']==States.idle:
            addWord(user, text)
    users.save(user)





def getUpdates():
    messeges = telegram.getUpdates(params['offset'])
    for u in messeges:
        if 'message' in u:
            if u['update_id'] < params['offset']:
                print('Error')
            else:
                chat_id = u['message']['chat']['id']
                text = u['message']['text']
                params['offset'] = max(params['offset'], u['update_id']+1)
                parseAction(chat_id, text)

    db.meta.save(params)

if __name__ == "__main__":
    global client
    global words
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true')
    args = parser.parse_args()
    secret_settings.configure(args.debug)



    ###LOGGING
    access = logging.FileHandler('access.log')
    access.setLevel(logging.INFO)
    access.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    error = logging.FileHandler('error.log')
    error.setLevel(logging.ERROR)
    error.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(access)
    logger.addHandler(error)
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Debug mode")


    db = MongoClient(secret_settings.mongo['uri']).telegram
    users = db.users



    params['offset'] = 0
    logging.warning('Started')
    while True:
        getUpdates()
        time.sleep(0.1)
    #app.run()
