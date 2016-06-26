import random
import telegram
import datetime
import study_settings
import copy

params = {}

langs = {

    1: {'original': 'en',
        'candidacies': 'ru'
        },
    2: {'original': 'ru',
        'candidacies': 'en'
        }
}

choose = 'Choose train type:\n' \
         '1-foreign->native\n' \
         '2-native->foreign\n' \
         '3-write foreign'


def do_train(user, string):
    if user['train']['type'] == 0:
        user['train']['type'] = -1
        telegram.send_message(user['chat_id'], choose, reply_markup=telegram.chooseTrainKeyboard)
    elif user['train']['type'] == -1:
        if string == 'end':
            end_train(user, string)
        else:
            user['train']['type'] = int(string)
            trains[user['train']['type']](user, string, overwrite=True)
    else:
        trains[user['train']['type']](user, string)


def do_variant_train(user, string, overwrite=False):
    out_str = ""
    was_incorrect = False
    lang_original = langs[user['train']['type']]['original']
    lang_candidacies = langs[user['train']['type']]['candidacies']
    if string[0] == '/':
        overwrite = True
    if not overwrite:

        try:
            a = int(string) - 1
        except ValueError:
            telegram.send_message(user['chat_id'], "Error parse!")
            return
        for w in user['words']:
            if w == user['train']['word']:
                if user['train']['correct'] == a:
                    out_str += "Correct\n"
                    if w['stage'] < study_settings.max_stage:
                        w['stage'] += 1
                    w['expiration_date'] = datetime.datetime.utcnow() + study_settings.stages[w['stage']]
                else:
                    out_str += "Incorrect\nThe correct one is %s \n" % (w[lang_candidacies],)
                    if w['stage'] > study_settings.min_stage:
                        w['stage'] -= 1
                    was_incorrect = True

    if len(list(filter(lambda _: _['expiration_date'] < datetime.datetime.utcnow(), user['words']))) > 8:
        if not was_incorrect:
            word_list = sorted(user['words'], key=lambda _: _['expiration_date'])[0:8]
            random.shuffle(word_list)
            word_list = word_list[0:4]
            user['train']['word_list'] = word_list
            cnt = random.randint(0, 3)
            user['train']['word'] = word_list[cnt]
            user['train']['correct'] = cnt
        out_str += user['train']['word'][lang_original] + "\n"
        for i, w in zip(range(4), user['train']['word_list']):
            out_str += "%s - %s\n" % (i + 1, w[lang_candidacies])
    else:
        out_str += "Not enough words\n"
        user['train']['type'] = 0
    if user['train']['type'] == 0:
        telegram.send_message(user['chat_id'], out_str, reply_markup=telegram.hideKeyboard)
    else:
        telegram.send_message(user['chat_id'], out_str, reply_markup=telegram.variantTrainKeyboard)


def do_translate_train(user, string, overwrite=False):
    out_str = ""
    was_incorrect = False
    if not overwrite:
        for w in user['words']:
            if w['ru'] == user['train']['word']['ru']:
                if w['en'].lower() == string.lower():
                    out_str += "Correct\n"
                    if w['stage'] < study_settings.max_stage:
                        w['stage'] += 1
                    w['expiration_date'] = datetime.datetime.utcnow() + study_settings.stages[w['stage']]
                else:
                    out_str += "Incorrect\nThe correct one is %s \n" % (w['en'],)
                    if w['stage'] > study_settings.min_stage:
                        w['stage'] -= 1
                    was_incorrect = True
    sup = list(filter(lambda _: _['expiration_date'] < datetime.datetime.utcnow() and
                                _['stage'] >= study_settings.min_translation_stage, user['words']))
    if len(sup) > 1:
        if not was_incorrect:
            word = copy.deepcopy(random.choice(sup))
            user['train']['word'] = word
            user['train']['shuffled'] = ''.join(random.sample(word['en'].lower(), len(word['en'])))
        out_str += user['train']['word']['ru'] + "\n"
        if 'shuffled' in user['train']:
            out_str += user['train']['shuffled'] + "\n"
    else:
        out_str += "Not enough words\n"
        user['train']['type'] = 0
    telegram.send_message(user['chat_id'], out_str, reply_markup=telegram.hideKeyboard)


trains = {
    1: do_variant_train,
    2: do_variant_train,
    3: do_translate_train
}


def end_train(self, user, string):
    if user['train']['type'] == 0:
        out_str = "No train is in process"
    else:
        out_str = "Train ended"
    user['train']['type'] = 0
    telegram.send_message(user['chat_id'], out_str, reply_markup=telegram.hideKeyboard)
