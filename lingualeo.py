import requests

#Dummy change
class LinguaLeo:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.cookies = {}

    def auth(self):
        url = "http://api.lingualeo.com/api/login"
        values = {
            "email": self.email,
            "password": self.password
        }
        self.make_request(url, values)

    def add_word(self, word, tword, context):
        url = "http://api.lingualeo.com/addword"
        values = {
            "word": word,
            "tword": tword,
            "context": context,
        }
        return self.make_request(url, values)

    def get_translates(self, word):
        url = "http://api.lingualeo.com/gettranslates"

        result = self.make_request(url,
                                   {word: word})
        if "translate" in result:
            word_list = [_["value"] for _ in result["translate"]]
            return {
                "is_exist": len(result["translate"])>0,
                "word": word,
                "word_list": word_list
            }
        return {
            "is_exist": False
        }

    def make_request(self, url, params):
        r = requests.get(url, params, cookies=self.cookies)
        self.cookies = r.cookies
        return r.json()


l = LinguaLeo("omrigann@gmail.com", 'Ling8597')
a = l.get_translates("Word")
print(a)
