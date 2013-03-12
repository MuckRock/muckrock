from muckrock.formwizard.storage.base import BaseStorage

class SessionStorage(BaseStorage):
    step_session_key = 'step'
    step_data_session_key = 'step_data'
    extra_context_session_key = 'extra_context'
    
    def __init__(self, prefix, request, *args, **kwargs):
        self.prefix = 'formwizard_%s' % prefix
        self.request = request
        if not self.request.session.has_key(self.prefix):
            self.init_storage()
        super(BaseStorage, self).__init__(*args, **kwargs)

    def init_storage(self):
        self.request.session[self.prefix] = {
            self.step_session_key: None,
            self.step_data_session_key: {},
            self.extra_context_session_key: {},
        }
        self.request.session.modified = True
        return True

    def get_current_step(self):
        return self.request.session[self.prefix][self.step_session_key]

    def set_current_step(self, step):
        self.request.session[self.prefix][self.step_session_key] = step
        self.request.session.modified = True
        return True

    def get_step_data(self, step):
        return self.request.session[self.prefix][self.step_data_session_key].get(step, None)

    def set_step_data(self, step, cleaned_data):
        self.request.session[self.prefix][self.step_data_session_key][step] = cleaned_data
        self.request.session.modified = True
        return True

    def get_extra_context_data(self):
        return self.request.session[self.prefix][self.extra_context_session_key] or {}

    def set_extra_context_data(self, extra_context):
        self.request.session[self.prefix][self.extra_context_session_key] = extra_context
        self.request.session.modified = True
        return True

    def reset(self):
        return self.init_storage()

    def update_response(self, response):
        return response

class DynamicSessionStorage(SessionStorage):
    form_list_session_key = 'form_list'

    def init_storage(self):
        super(DynamicSessionStorage, self).init_storage()
        self.request.session[self.prefix][self.form_list_session_key] = []
        self.request.session.modified = True
        return True

    def get_form_list(self):
        return self.request.session[self.prefix][self.form_list_session_key] or []

    def set_form_list(self, form_list):
        self.request.session[self.prefix][self.form_list_session_key] = form_list
        self.request.session.modified = True
        return True

