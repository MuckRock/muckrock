class BaseStorage(object):
    def __init__(self, prefix, *args, **kwargs):
        self.prefix = 'formwizard_%s' % prefix
        super(BaseStorage, self).__init__(*args, **kwargs)

    def get_current_step(self):
        raise NotImplementedError()

    def set_current_step(self, step):
        raise NotImplementedError()

    def get_step_data(self, step):
        raise NotImplementedError()

    def set_step_data(self, step, cleaned_data):
        raise NotImplementedError()

    def get_extra_context_data(self):
        raise NotImplementedError()

    def set_extra_context_data(self, extra_context):
        raise NotImplementedError()

    def reset(self):
        raise NotImplementedError()

    def update_response(self, response):
        raise NotImplementedError()
