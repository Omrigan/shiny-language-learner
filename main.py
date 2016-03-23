from flask import Flask
from pymongo import MongoClient
import secret_settings, study_settings
import telegram
import my_correction
from nltk.stem import WordNetLemmatizer
import traceback, sys
import train, remainder
import random, re, os
from enum import Enum

import time, datetime
import logging, argparse
from xml.etree import ElementTree
from bs4 import BeautifulSoup
import requests
env = os.getenv('BOT_ENV', 'staging')

class States():
    idle = 1
    translates_proposed = 2



logger = logging.getLogger("bot")
help_text = open('docs/help.txt').read()
changelog_text = open('docs/changelog.txt').read()
wnl = WordNetLemmatizer()

def correct(string):
    baseurl_correction = 'http://service.afterthedeadline.com/checkDocument'
    correction = requests.get(baseurl_correction, {'data': string}).text
    correction = BeautifulSoup(correction, "lxml")


    if correction.find("option") is not None:
        string = correction.find("option").string
    return string

def addWord(user, string):
    baseurl = 'https://translate.yandex.net/api/v1.5/tr.json/translate'
    string = re.sub(r'[^A-Za-z\s]', '', string)
    string = re.sub(r'\Wk+', ' ', string)
    string = string.lower()

    if len(string) == 0:
        telegram.sendMessage(user['chat_id'], "Wrong word")
        return


    #string = correct(string)
    string =my_correction.correct(string)
    t = time.time()
    if env!='debug':
        string = wnl.lemmatize(string)
    print(time.time() - t, ' secs')
    string = string[0].upper() + string[1:]
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

def startTrain(user, text):
    user['train']['type'] = 0
    train.doTrain(user, text)

def addReamainder(user, text):
    remainder.remove_job(user)
    tokens = text.split(' ')
    delta = datetime.timedelta()
    if len(tokens)>=2:
        tokens=tokens[1].replace(' ', '').split(':')
        hours = int(tokens[0])
        minutes = int(tokens[1])
        delta = datetime.timedelta(hours=hours, minutes=minutes)
    remainder.add_job(user, datetime.datetime.utcnow()+delta)
    telegram.sendMessage(user['chat_id'], "Successfully set. Nearest at  %s" % (datetime.datetime.now()+delta,))

def removeRemainder(user, text):
    remainder.remove_job(user)
    telegram.sendMessage(user['chat_id'], "Removed")

comands = {
    'eraselast': eraseLastWord,
    'getlist': getListWord,
    'starttrain': startTrain,
    'endtrain': train.endTrain,
    'start': start,
    'help': help,
    'setremainder': addReamainder,
    'removeremainder': removeRemainder
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
        cmd = text[1:].lower().split(' ')[0]
        if cmd in comands:
            comands[cmd](user, text)
    else:
        if user['train']['type']!=0:
            train.doTrain(user, text)
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
                try:
                    parseAction(chat_id, text)
                except Exception:
                    logging.error('Error! (%s, %s)' %(chat_id, text))
                    logging.error(traceback.print_exc())
                    telegram.sendMessage(chat_id, 'Parse error! Try again')

    db.meta.save(params)

if __name__ == "__main__":
    global client
    global words


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
    if not  db.validate_collection('users'):
        db.create_collection('users')
    users = db.users



    params['offset'] = 0
    logging.warning('Started')
    while True:
        getUpdates()
        time.sleep(0.1)
    #app.run()
