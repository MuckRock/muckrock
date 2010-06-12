import hmac

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.utils.hashcompat import sha_constructor
from django.utils import simplejson as json
from formwizard.storage.base import BaseStorage

sha_hmac = sha_constructor

class CookieStorage(BaseStorage):
    step_cookie_key = 'step'
    step_data_cookie_key = 'step_data'
    extra_context_cookie_key = 'extra_context'

    def __init__(self, prefix, request, *args, **kwargs):
        self.prefix = 'formwizard_%s' % prefix
        self.request = request
        self.cookie_data = self.load_cookie_data()
        if self.cookie_data is None:
            self.init_storage()
        super(BaseStorage, self).__init__(*args, **kwargs)

    def init_storage(self):
        self.cookie_data = {
            self.step_cookie_key: None,
            self.step_data_cookie_key: {},
            self.extra_context_cookie_key: {},
        }
        return True

    def get_current_step(self):
        return self.cookie_data[self.step_cookie_key]

    def set_current_step(self, step):
        self.cookie_data[self.step_cookie_key] = step
        return True

    def get_step_data(self, step):
        return self.cookie_data[self.step_data_cookie_key].get(step, None)

    def set_step_data(self, step, cleaned_data):
        self.cookie_data[self.step_data_cookie_key][step] = cleaned_data
        return True

    def get_extra_context_data(self):
        return self.cookie_data[self.extra_context_cookie_key] or {}

    def set_extra_context_data(self, extra_context):
        self.cookie_data[self.extra_context_cookie_key] = extra_context
        return True

    def reset(self):
        return self.init_storage()

    def update_response(self, response):
        if len(self.cookie_data) > 0:
            response.set_cookie(self.prefix, self.create_cookie_data(self.cookie_data))
        else:
            response.delete_cookie(self.prefix)
        return response

    def load_cookie_data(self):
        data = self.request.COOKIES.get(self.prefix, None)
        if data is None:
            return None

        bits = data.split('$', 1)
        if len(bits) == 2:
            if bits[0] == self.get_cookie_hash(bits[1]):
                return json.loads(bits[1], cls=json.JSONDecoder)

        raise SuspiciousOperation('FormWizard cookie manipulated')

    def get_cookie_hash(self, data):
        return hmac.new('%s$%s' % (settings.SECRET_KEY, self.prefix), data, sha_hmac).hexdigest()

    def create_cookie_data(self, data):
        encoder = json.JSONEncoder(separators=(',', ':'))
        encoded_data = encoder.encode(data)
        return '%s$%s' % (self.get_cookie_hash(encoded_data), encoded_data)
