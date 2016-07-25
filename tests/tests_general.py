import unittest
import requests
import copy

from language_learner_env import secret_settings

class ApiTest(unittest.TestCase):
    user = {'hello'}
    base_url = 'https://api.telegram.org/bot'


    def get_me(self, token):
        url = self.base_url + token + '/getMe'
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200)
        return resp.json()

    def test_prod(self):
        self.assertEqual(self.get_me(secret_settings.bot_prod['token'])['result']['username'],'word_repeater_bot')

    def test_debug(self):
        self.assertEqual(self.get_me(secret_settings.bot_debug['token'])['result']['username'], 'word_repeater_test_bot')