from flask import Flask
from pymongo import MongoClient
import secret_settings, study_settings
import telegram

from train import startTrain, endTrain
import random
from enum import Enum

import time, datetime
import logging
from xml.etree import ElementTree
from bs4 import BeautifulSoup
import requests
app = Flask(__name__)


class States():
    idle = 1
    translates_proposed = 2





def addWord(user, string):
    baseurl = 'https://translate.yandex.net/api/v1.5/tr.json/translate'
    #correct = requests.get('http://suggestqueries.google.com/complete/search?client=firefox&q=%s' %(string)).json()
    baseurl_correction = 'http://service.afterthedeadline.com/checkDocument'
    correction = requests.get(baseurl_correction, {'data': string}).text
    correction = BeautifulSoup(correction)


    if correction.find("option") is not None:
        string = correction.find("option").string
    string = string[0].upper() + string[1:]

    transtaltion = requests.get(baseurl, {
        'key': secret_settings.translate_yandex['token'],
        'lang': 'ru',
        'text': string
    })

    out_word = transtaltion.json()['text'][0]
#     out_str = "Choose from following:\n"
#     for i, w in zip(range(len(user['wordlist'])), user['wordlist']):
#         out_str += '%s - %s' %(1+i, w)
#     postUpdate(id, out_str)
#     user['state'] = States.translates_proposed
# elif user['state'] == States.translates_proposed:
#     val = int(string)-1
#     out_word = user['wordlist'][val]
    already_has = False
    for w in user['words']:
        already_has |= w["en"]==string
    if not already_has:
        user['words'].append({"en": string, "ru": out_word,
                              "stage": 1,
                              "expiration_date": datetime.datetime.utcnow() + study_settings.stages[1],
                              "creation_date": datetime.datetime.utcnow()})
        users.save(user)
        telegram.sendMessage(user['chat_id'], "Word added\n%s - %s" % (string, out_word))
    else:
        telegram.sendMessage(user['chat_id'], 'Already exist!')

params = {}

def eraseLastWord(user, text):
    if(len(user['words'])>0):
        str_out = "%s - %s" % (user['words'][-1]['en'], user['words'][-1]['ru'])
        user['words'] = user['words'][:-1]
        telegram.sendMessage(user['chat_id'], "Last word erased\n" + str_out)

def getListWord(user, text):
    str_out = "\n".join(["%s - %s" % (w['en'], w['ru']) for w in user['words']])
    telegram.sendMessage(user['chat_id'], str_out)


comands = {
    'eraselast': eraseLastWord,
    'getlist': getListWord,
    'starttrain': startTrain,
    'endtrain': endTrain,
}

def parseAction(chat_id, text):
    logging.info("%s - %s" %(chat_id, text))
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

    db.meta.update({'_id' : params['_id']}, params)

@app.route("/")
def hello():
    pass


if __name__ == "__main__":
    global client
    global words
    logging.basicConfig(level=logging.INFO)
    db = MongoClient(secret_settings.mongo['host']).telegram
    users = db.users
    params  = db.meta.find_one()
    params['offset'] = 0
    while True:
        getUpdates()
        time.sleep(0.1)
    #app.run()
