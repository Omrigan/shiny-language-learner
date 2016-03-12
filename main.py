from flask import Flask
from pymongo import MongoClient
import settings
from enum import Enum
import time

import requests
app = Flask(__name__)


class States(Enum):
    idle = 1
    translates_proposed = 2
    train = 3



user = {
    'state': States.idle,
    'wordlist': []
}


def postUpdate(id, string):
    baseurl = 'https://api.telegram.org/bot'
    url = baseurl + settings.bot['token'] + '/sendMessage'
    resp = requests.get(url, params={
        'chat_id': id,
        'text': string,
    })
    # params['offset']+=1
    # db.meta.update({'_id' : params['_id']}, params)


def processString(id, string):
    print (string)
    if user['state']==States.idle:
        baseurl = 'https://translate.yandex.net/api/v1.5/tr.json/translate'
        transtaltion = requests.get(baseurl, {
            'key': settings.translate_yandex['token'],
            'lang': 'ru',
            'text': string
        })
        user['wordlist'] = transtaltion.json()['text']
        out_str = "Choose from following:\n"
        for i, w in zip(range(len(user['wordlist'])), user['wordlist']):
            out_str += '%s - %s' %(1+i, w)
        postUpdate(id, out_str)
        user['state'] = States.translates_proposed
    elif user['state'] == States.translates_proposed:
        val = int(string)-1
        out_word = user['wordlist'][val]
        postUpdate(id, "Word added " + out_word)
        user['state'] = States.idle





params = {}

def getUpdates():
    baseurl = 'https://api.telegram.org/bot'
    url = baseurl + settings.bot['token'] + '/getUpdates'

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
                processString(chat_id, text)

    db.meta.update({'_id' : params['_id']}, params)

@app.route("/")
def hello():
    pass


if __name__ == "__main__":
    global client
    global words
    db = MongoClient(settings.mongo['host']).telegram
    words = db.words
    params  = db.meta.find_one()
    params['offset'] = 0
    while True:
        getUpdates()
        time.sleep(0.1)
    #app.run()
