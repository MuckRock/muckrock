===============
Getting started
===============
This tutorial shows the basic functionality of **django-formwizard**.

We will build a multi-step feedback form and use the first example to introduce the named-url formwizard.

Before we start, make sure that you installed **django-formwizard** either using the pypi package:

.. code-block:: console

    # pip install django-formwizard

or the maybe-not stable development version on GitHub:

.. code-block:: console

    # pip install -e git+git://github.com/stephrdev/django-formwizard.git#egg=django-formwizard

Defining our single step forms
==============================
**django-formwizard** used no special forms. Just create some `Form` classes, `ModelForm` classes or create one or more `FormSet`.

But remember, file uploads won't work!

.. code-block:: python

    class FeedbackStep1(forms.Form):
        name = forms.CharField()
        email = forms.EmailField()

    class FeedbackStep2(forms.Form):
        support = forms.ChoiceField(choices=(('like', 'like it'), \
            ('dontlike', 'dont like it')))
        performance = forms.ChoiceField(choices=(('like', 'like it'), \
            ('dontlike', 'dont like it')))

    class FeedbackStep3(forms.Form):
        message = forms.CharField(widget=forms.Textarea())

Creating our formwizard class
=============================

To use the formwizard, you have to subclass `formwizard.forms.FormWizard` and add at least a `done` method. There are much more methods you could override. But now, there is no need for it.

If you use `formwizard.forms.FormWizard`, you have to define a storage backend manually. To get rid of this, django-formwizard provides to predefined storage backend formwizards. SessionFormWizard and CookieFormWizard. The SessionFormWizard will store the step-formdata in a session and the CookieFormWizard will save the formdata in a cookie (which is protected against manipulation).

For example, the formwizard will look for a template in the template directory using the following filename: `formwizard/wizard.html`. But this file is no complete html page. It has not <form> tags or <body>/<html> stuff. To change this behaviour, you can override the `get_template` method and return a list of templates to use.

The `done` method in this example will render the template `support/done.html` and add a list of the cleaned_data dictionaries.

.. code-block:: python

    from formwizard.forms import SessionFormWizard

    class FeedbackWizard(SessionFormWizard):
        def done(self, request, form_list):
            return render_to_response(
                'support/done.html',
                {'form_list': [form.cleaned_data for form in form_list]},
                context_instance=RequestContext(request)
            )

        def get_template(self):
            return ['support/form.html',]

Create the formwizard instance
==============================

To actually use the form wizard, we have to create a can be done once (if you don't need need to add initial data/instance data) or within a view.

.. code-block:: python

    feedback_form_instance = FeedbackWizard([FeedbackStep1, FeedbackStep2, \
        FeedbackStep3])

After creating the form wizard instance, we need to make the wizard public accessible using a `urls.py`.

.. code-block:: python

    urlpatterns = patterns('',
        url(r'^$', feedback_form_instance, name='feedback_wizard'),
    )

Basic template for our formwizard
=================================

To render the wizard and the done-page, we have to add some templates.

support/form.html
-----------------

.. code-block:: html
    
    <html>
        <head>
            <title>Feedback</title>
        </head>
        <body>
            <h1>We want your feedback!</h1>
            <form action="." method="post">
                {% include "formwizard/wizard.html" %}
            </form>
        </body>
    </html>

support/done.html
-----------------

.. code-block:: html

    <html>
        <head>
            <title>Feedback Done</title>
        </head>
        <body>
            <h1>We got your feedback!</h1>
            <pre>
                {{ form_list|pprint }}
            </pre>
        </body>
    </html>

The done-page will just print out all cleaned_data key/values.

What's next
===========

You could add a nice **Thank you** template and send a mail to the site's managers instead of displaying the formdata.
