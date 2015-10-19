from muckrock.accounts.models import Profile
p = Profile.objects.first()
p.activity_email()
