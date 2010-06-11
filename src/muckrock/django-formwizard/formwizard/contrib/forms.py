from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from formwizard.forms import SessionFormWizard

class NamedUrlSessionFormWizard(SessionFormWizard):
    done_step_name = 'done'

    def __init__(self, *args, **kwargs):
        assert kwargs.has_key('url_name'), 'url name is needed to resolve correct wizard urls'
        self.url_name = kwargs['url_name']
        del kwargs['url_name']
        if kwargs.has_key('done_step_name'):
            self.done_step_name = kwargs['done_step_name']
            del kwargs['done_step_name']
        super(NamedUrlSessionFormWizard, self).__init__(*args, **kwargs)
        assert not self.form_list.has_key(self.done_step_name), 'step name "%s" is reserved for the "done" view' % self.done_step_name

    def process_get_request(self, *args, **kwargs):
        if not kwargs.has_key('step'):
            if self.request.GET.has_key('reset'):
                self.reset_wizard()
                self.storage.set_current_step(self.get_first_step())
            if 'extra_context' in kwargs:
                self.update_extra_context(kwargs['extra_context'])
            return HttpResponseRedirect(reverse(self.url_name, kwargs={'step': self.determine_step()}))
        else:
            if 'extra_context' in kwargs:
                self.update_extra_context(kwargs['extra_context'])
            step_url = kwargs.get('step', None)
            if step_url == self.done_step_name:
                return self.render_done(self.get_form(step=self.get_last_step(), data=self.storage.get_step_data(self.get_last_step())), *args, **kwargs)
            if step_url <> self.determine_step():
                if self.form_list.has_key(step_url):
                    self.storage.set_current_step(step_url)
                    return self.render(self.get_form(data=self.storage.get_step_data(self.storage.get_current_step())))
                else:
                    self.storage.set_current_step(self.get_first_step())
                return HttpResponseRedirect(reverse(self.url_name, kwargs={'step': self.storage.get_current_step()}))
            else:
                return self.render(self.get_form(data=self.storage.get_step_data(self.storage.get_current_step())))

    def process_post_request(self, *args, **kwargs):
        if self.request.POST.has_key('form_prev_step') and self.form_list.has_key(self.request.POST['form_prev_step']):
            self.storage.set_current_step(self.request.POST['form_prev_step'])
            return HttpResponseRedirect(reverse(self.url_name, kwargs={'step': self.storage.get_current_step()}))
        else:
            return super(NamedUrlSessionFormWizard, self).process_post_request(*args, **kwargs)

    def render_next_step(self, form, *args, **kwargs):
        next_step = self.get_next_step()
        self.storage.set_current_step(next_step)
        return HttpResponseRedirect(reverse(self.url_name, kwargs={'step': next_step}))

    def render_revalidation_failure(self, step, form):
        self.storage.set_current_step(step)
        return HttpResponseRedirect(reverse(self.url_name, kwargs={'step': self.storage.get_current_step()}))

    def render_done(self, *args, **kwargs):
        step_url = kwargs.get('step', None)
        if step_url <> self.done_step_name:
            return HttpResponseRedirect(reverse(self.url_name, kwargs={'step': self.done_step_name}))
        return super(NamedUrlSessionFormWizard, self).render_done(*args, **kwargs)
