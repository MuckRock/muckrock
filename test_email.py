import actstream
from muckrock.accounts.models import Profile
p = Profile.objects.first()
u = p.user
s = actstream.models.user_stream(u)
p.activity_email(s)
