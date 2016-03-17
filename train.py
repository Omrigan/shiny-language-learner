import random, telegram
import datetime
import study_settings

params = {}


def startTrain(user, string):
    out_str = ""
    was_incorrect = False
    if(user['train']['type']==1 and string!='/starttrain'):
        if string=='del':
            for w in user['words']:
                if w['en']==user['train']['word']:
                    user['words'].remove(w)
                    telegram.sendMessage(user['chat_id'], "Deleted")

        else:
            try:
                a = int(string) - 1
            except ValueError:
                telegram.sendMessage(user['chat_id'], "Error parse!")
                return
            for w in user['words']:
                if w['en']==user['train']['word']:
                    if user['train']['correct']==a:
                        out_str+="Correct\n"
                        if w['stage']<study_settings.max_stage:
                            w['stage']+=1
                        w['expiration_date'] = datetime.datetime.utcnow() + study_settings.stages[w['stage']]
                    else:
                        out_str+="Incorrect\nThe correct one is %s \n" %(w['ru'],)
                        if w['stage']>study_settings.min_stage:
                            w['stage']-=1
                        was_incorrect=True

    if len(list(filter(lambda w: w['expiration_date'] < datetime.datetime.utcnow(), user['words'])))>8:
        if not was_incorrect:
            user['train']['type'] = 1
            wordlist = sorted(user['words'], key=lambda x: x['expiration_date'])[0:8]
            random.shuffle(wordlist)
            wordlist = wordlist[0:4]
            user['train']['wordlist'] = wordlist
            cnt = random.randint(0, 3)
            user['train']['word'] = wordlist[cnt]['en']
            user['train']['correct'] = cnt
        out_str += user['train']['word'] + "\n"
        for i, w in zip(range(4), user['train']['wordlist']):
            out_str += "%s - %s\n" % (i+1, w['ru'])
        out_str += 'Print "del" to delete this word'
    else:
        out_str += "No words\n"
        user['train']['type'] = 0
    telegram.sendMessage(user['chat_id'], out_str)

def endTrain(user, string):
    user['train']['type'] = 0
    telegram.sendMessage(user['chat_id'], "Train ended")
