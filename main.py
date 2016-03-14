from flask import Flask
from pymongo import MongoClient
import secret_settings
import random
from enum import Enum

import time, datetime
from xml.etree import ElementTree
from bs4 import BeautifulSoup
import requests
app = Flask(__name__)


class States():
    idle = 1
    translates_proposed = 2



def sendMessage(chat_id, string):
    baseurl = 'https://api.telegram.org/bot'
    url = baseurl + secret_settings.bot['token'] + '/sendMessage'
    resp = requests.get(url, params={
        'chat_id': chat_id,
        'text': string,
    })

stages = {
    1: datetime.timedelta(hours=0),
    2: datetime.timedelta(hours=8),
    3: datetime.timedelta(hours=24),
    4: datetime.timedelta(weeks=100)
}

def startTrain(user, string):
    out_str = ""
    if(user['train']['type']==1):
        try:
            a = int(string)
        except ValueError:
            sendMessage(user['chat_id'], "Error parse!")
            return
        for w in user['words']:
            if w['en']==user['train']['word']:
                if user['train']['correct']==a:
                    out_str+="Correct\n"
                    w['stage']+=1
                    w['expiration_date'] = datetime.datetime.utcnow() + stages[w['stage']]
                else:
                    out_str+="Incorrect\n"

    if len(list(filter(lambda w: w['expiration_date'] < datetime.datetime.utcnow(), user['words'])))>8:
        user['train']['type'] = 1
        wordlist = sorted(user['words'], key=lambda x: x['expiration_date'])[0:8]
        random.shuffle(wordlist)
        wordlist = wordlist[0:4]
        cnt = random.randint(0, 3)
        user['train']['word'] = wordlist[cnt]['en']
        user['train']['correct'] = cnt
        out_str += user['train']['word'] + "\n"
        for i, w in zip(range(4), wordlist):
            out_str += "%s - %s\n" % (i, w['ru'])
    else:
        out_str += "No words\n"
        user['train']['type'] = 0
    sendMessage(user['chat_id'], out_str)

def endTrain(user, string):
    user['train']['type'] = 0
    sendMessage(user['chat_id'], "Train ended")





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
                              "expiration_date": datetime.datetime.utcnow() + stages[1],
                              "creation_date": datetime.datetime.utcnow()})
        users.save(user)
        sendMessage(user['chat_id'], "Word added\n%s - %s" % (string, out_word))
    else:
        sendMessage(user['chat_id'], 'Already exist!')

params = {}

def eraseLastWord(user, text):
    if(len(user['words'])>0):
        str_out = "%s - %s" % (user['words'][-1]['en'], user['words'][-1]['ru'])
        user['words'] = user['words'][:-1]
        sendMessage(user['chat_id'], "Last word erased\n" + str_out)

def getListWord(user, text):
    str_out = "\n".join(["%s - %s" % (w['en'], w['ru']) for w in user['words']])
    sendMessage(user['chat_id'], str_out)


comands = {
    'eraselast': eraseLastWord,
    'getlist': getListWord,
    'starttrain': startTrain,
    'endtrain': endTrain,
}


def parseAction(chat_id, text):
    print (text)
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
    baseurl = 'https://api.telegram.org/bot'
    url = baseurl + secret_settings.bot['token'] + '/getUpdates'
    updates = requests.get(url, {
        'offset': params['offset']
    })
    messeges = updates.json()['result']
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
    db = MongoClient(secret_settings.mongo['host']).telegram
    users = db.users
    params  = db.meta.find_one()
    params['offset'] = 0
    while True:
        getUpdates()
        time.sleep(0.1)
    #app.run()
