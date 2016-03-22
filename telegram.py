import secret_settings, requests
import logging
import json
baseurl = 'https://api.telegram.org/bot'


logger = logging.getLogger("bot")
variantTrainKeyboard= json.dumps({
        'keyboard': [
        ['1', '3'],
        ['2', '4'],
        ['del', 'end']
    ],
       'resize_keyboard': True
    })
chooseTrainKeyboard= json.dumps({
        'keyboard': [
        ['1', '2', '3'],
        ['end']

    ],
       'resize_keyboard': True
    })

hideKeyboard = json.dumps({
    'hide_keyboard': True,

})



def sendMessage(chat_id, string, *args, **kwargs):
    url = baseurl + secret_settings.bot['token'] + '/sendMessage'
    params={
        'chat_id': chat_id,
        'text': string,
        'timeout': 20,
    }
    if 'reply_markup' in kwargs:
        params['reply_markup'] = kwargs['reply_markup']
    resp = requests.get(url, params)
    if resp.status_code!=200:
        logger.error("Cannot send message %s - %s" % (chat_id, string))
    return resp

def getUpdates(offset):
    baseurl = 'https://api.telegram.org/bot'
    url = baseurl + secret_settings.bot['token'] + '/getUpdates'
    updates = requests.get(url, {
        'offset': offset,
        'timeout': 20,
    })
    if updates.status_code!=200:
        logger.error("Cannot get updates %s" % (offset, ))
    return updates.json()['result']




