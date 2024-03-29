# Generated by Django 2.2.15 on 2021-04-08 16:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0046_auto_20210304_1059'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flaggedtask',
            name='category',
            field=models.TextField(blank=True, choices=[('move communication', 'A communication ended up on this request inappropriately.'), ('no response', 'This agency has not responded after multiple submissions.'), ('wrong agency', 'The agency has indicated that this request should be directed to another agency.'), ('missing documents', 'I should have received documents for this request.'), ('form', 'The agency has asked that you use a form.'), ('follow-up complaints', 'Agency is complaining about follow-up messages.'), ('appeal', 'Should I appeal this response?'), ('proxy', 'The agency denied the request due to an in-state citzenship law.'), ('contact info changed', 'User supplied contact info.'), ('no proxy', 'No proxy was available.'), ('agency login confirm', 'An agency used a secure login to update a request.'), ('agency login validate', 'An agency used an insecure login to update a request.'), ('agency new email', 'An agency with no primary email set replied via email.'), ('manual form', 'A request needs a PDF form to be manually filled out to be submitted'), ('foiaonline', 'The FOIAOnline autologin failed'), ('download file', 'This request contains a link to a file to download'), ('already responded', 'I already responded to this request'), ('bad contact', 'I am not the best contact for this request'), ('wrong agency', 'This request should go to a different agency')]),
        ),
    ]
