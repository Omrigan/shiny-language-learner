import random, telegram
import datetime
import study_settings

params = {}

langs = {

    1: {'original': 'en',
     'candidacies': 'ru'
     },
    2: {'original': 'ru',
     'candidacies': 'en'
     }
}

train_names = {
    'eng->rus': 1,
    'rus->eng': 2,
    'write eng': 3
}



choose = 'Choose train type:\n' \
         '1-eng->rus\n' \
         '2-rus->eng\n' \
         '3-write eng'

def doTrain(user, string):
    if user['train']['type']==0:
        user['train']['type'] = -1
        telegram.sendMessage(user['chat_id'], choose, reply_markup=telegram.chooseTrainKeyboard)
    elif user['train']['type']==-1:
        if string=='end':
            endTrain(user,string)
        else:
            user['train']['type'] = int(string)
            trains[user['train']['type']](user, string, overwrite=True)
    else:
        trains[user['train']['type']](user, string)



def doVariantTrain(user, string, overwrite=False):
    out_str = ""
    was_incorrect = False
    lang_original = langs[user['train']['type']]['original']
    lang_candidacies = langs[user['train']['type']]['candidacies']
    if(not overwrite):
        if string=='del':
            for w in user['words']:
                if w[lang_original]==user['train']['word']:
                    user['words'].remove(w)
                    telegram.sendMessage(user['chat_id'], "Deleted")
        elif string=='end':
            endTrain(user, string)
            return
        else:
            try:
                a = int(string) - 1
            except ValueError:
                telegram.sendMessage(user['chat_id'], "Error parse!")
                return
            for w in user['words']:
                if w[lang_original]==user['train']['word']:
                    if user['train']['correct']==a:
                        out_str+="Correct\n"
                        if w['stage']<study_settings.max_stage:
                            w['stage']+=1
                        w['expiration_date'] = datetime.datetime.utcnow() + study_settings.stages[w['stage']]
                    else:
                        out_str+="Incorrect\nThe correct one is %s \n" %(w[lang_candidacies],)
                        if w['stage']>study_settings.min_stage:
                            w['stage']-=1
                        was_incorrect=True

    if len(list(filter(lambda w: w['expiration_date'] < datetime.datetime.utcnow(), user['words'])))>8:
        if not was_incorrect:

            wordlist = sorted(user['words'], key=lambda x: x['expiration_date'])[0:8]
            random.shuffle(wordlist)
            wordlist = wordlist[0:4]
            user['train']['wordlist'] = wordlist
            cnt = random.randint(0, 3)
            user['train']['word'] = wordlist[cnt][lang_original]
            user['train']['correct'] = cnt
        out_str += user['train']['word'] + "\n"
        for i, w in zip(range(4), user['train']['wordlist']):
            out_str += "%s - %s\n" % (i+1, w[lang_candidacies])
        out_str += 'Print "del" to delete this word'
    else:
        out_str += "Not enough words\n"
        user['train']['type'] = 0
    if user['train']['type'] == 0:
        telegram.sendMessage(user['chat_id'], out_str, reply_markup=telegram.hideKeyboard)
    else:
        telegram.sendMessage(user['chat_id'], out_str, reply_markup=telegram.variantTrainKeyboard)


def doTranslateTrain(user, string, overwrite=False):
    out_str=""
    was_incorrect = False
    if(not overwrite):
        for w in user['words']:
            if w['ru']==user['train']['word']:
                if w['en'].lower()==string.lower():
                    out_str+="Correct\n"
                    if w['stage']<study_settings.max_stage:
                        w['stage']+=1
                    w['expiration_date'] = datetime.datetime.utcnow() + study_settings.stages[w['stage']]
                else:
                    out_str+="Incorrect\nThe correct one is %s \n" %(w['en'],)
                    if w['stage']>study_settings.min_stage:
                        w['stage']-=1
                    was_incorrect=True
    sup = list(filter(lambda w: w['expiration_date'] < datetime.datetime.utcnow() and
                    w['stage']>=study_settings.min_translation_stage, user['words']))
    if len(sup)>1:
        if not was_incorrect:
            random.shuffle(sup)
            user['train']['word'] = sup[0]['ru']
        out_str += user['train']['word'] + "\n"
        #out_str += 'Print "del" to delete this word'
    else:
        out_str += "Not enough words\n"
        user['train']['type'] = 0
    telegram.sendMessage(user['chat_id'], out_str, reply_markup=telegram.hideKeyboard)





trains = {
    1: doVariantTrain,
    2: doVariantTrain,
    3: doTranslateTrain
}

def endTrain(user, string):
    user['train']['type'] = 0
    telegram.sendMessage(user['chat_id'], "Train ended", reply_markup=telegram.hideKeyboard)
