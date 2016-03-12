from flask import Flask
from pymongo import MongoClient
import settings
from enum import Enum
import time
from xml.etree import ElementTree
from bs4 import BeautifulSoup
import requests
app = Flask(__name__)


class States():
    idle = 1
    translates_proposed = 2
    train = 3






def postUpdate(chat_id, string):
    baseurl = 'https://api.telegram.org/bot'
    url = baseurl + settings.bot['token'] + '/sendMessage'
    resp = requests.get(url, params={
        'chat_id': chat_id,
        'text': string,
    })
    # params['offset']+=1
    # db.meta.update({'_id' : params['_id']}, params)
def etree_to_dict(t):
    return {t.tag : map(etree_to_dict, t.iterchildren()) or t.text}

def processString(chat_id, string):
    print (string)
    user = users.find_one({'chat_id': chat_id})
    if user is None:
        user = {'chat_id': chat_id,
                'state': States.idle,
                'words': []}
    if user['state']==States.idle:
        baseurl = 'https://translate.yandex.net/api/v1.5/tr.json/translate'
        #correct = requests.get('http://suggestqueries.google.com/complete/search?client=firefox&q=%s' %(string)).json()
        baseurl_correction = 'http://service.afterthedeadline.com/checkDocument'
        correction = requests.get(baseurl_correction, {'data': string}).text
        correction = BeautifulSoup(correction)


        if correction.find("option") is not None:
            string = correction.find("option").string
        string = string[0].upper() + string[1:]

        transtaltion = requests.get(baseurl, {
            'key': settings.translate_yandex['token'],
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
        user['words'].append((string, out_word))
        users.save(user)
        postUpdate(user['chat_id'], "Word added\n%s - %s" % (string, out_word))






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
    users = db.users
    params  = db.meta.find_one()
    params['offset'] = 0
    while True:
        getUpdates()
        time.sleep(0.1)
    #app.run()
