from http.client import HTTPSConnection
from base64 import b64encode
from json import loads
from json import dumps
import environ

env = environ.Env()

DATA_FOR_SEO_LOGIN = env('DATA_FOR_SEO_LOGIN')
DATA_FOR_SEO_PASSWORD = env('DATA_FOR_SEO_PASSWORD')

class DataForSEORestClient:
    domain = "api.dataforseo.com"

    def __init__(self, username=None, password=None):
        self.username = DATA_FOR_SEO_LOGIN
        self.password = DATA_FOR_SEO_PASSWORD

    def request(self, path, method, data=None):
        connection = HTTPSConnection(self.domain)
        try:
            base64_bytes = b64encode(
                ("%s:%s" % (self.username, self.password)).encode("ascii")
                ).decode("ascii")
            headers = {'Authorization' : 'Basic %s' %  base64_bytes}
            connection.request(method, path, headers=headers, body=data)
            response = connection.getresponse()
            return loads(response.read().decode())
        finally:
            connection.close()

    def get(self, path):
        return self.request(path, 'GET')

    def post(self, path, data):
        if isinstance(data, str):
            data_str = data
        else:
            data_str = dumps(data)
        return self.request(path, 'POST', data_str)