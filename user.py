from pymongo import MongoClient
import secret_settings
db = MongoClient(secret_settings.mongo['uri']).telegram
users = db.users
class States():
    idle = 1
    translates_proposed = 2

class User:
    def User(self, chat_id):
        self.chat_id = chat_id
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
        self.state = user['State']
        self.words = user['words']
        self.train = users['train']