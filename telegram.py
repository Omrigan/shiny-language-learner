import secret_settings, requests
import logging
baseurl = 'https://api.telegram.org/bot'


logger = logging.getLogger("bot")
def sendMessage(chat_id, string):
    url = baseurl + secret_settings.bot['token'] + '/sendMessage'
    resp = requests.get(url, params={
        'chat_id': chat_id,
        'text': string,
    })
    if resp.status_code!=200:
        logger.error("Cannot send message %s - %s" % (chat_id, string))
    return resp

def getUpdates(offset):
    baseurl = 'https://api.telegram.org/bot'
    url = baseurl + secret_settings.bot['token'] + '/getUpdates'
    updates = requests.get(url, {
        'offset': offset
    })
    if updates.status_code!=200:
        logger.error("Cannot get updates %s" % (offset, ))
    return updates.json()['result']
