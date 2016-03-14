import secret_settings, requests

def sendMessage(chat_id, string):
    baseurl = 'https://api.telegram.org/bot'
    url = baseurl + secret_settings.bot['token'] + '/sendMessage'
    resp = requests.get(url, params={
        'chat_id': chat_id,
        'text': string,
    })
def getUpdates(offset):
    baseurl = 'https://api.telegram.org/bot'
    url = baseurl + secret_settings.bot['token'] + '/getUpdates'
    updates = requests.get(url, {
        'offset': offset
    })
    return updates.json()['result']