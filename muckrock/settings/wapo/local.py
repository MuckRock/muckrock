from muckrock.settings.local import *
from muckrock.settings.wapo.base import *

AWS_STORAGE_BUCKET_NAME="wp-muckrock-dev"
AWS_MEDIA_BUCKET_NAME="wp-muckrock-uploads-dev"
CLOUDFRONT_DOMAIN="wp-muckrock-dev.news-engineering.aws.wapo.pub"
AWS_STORAGE_DEFAULT_ACL="private"
AWS_MEDIA_QUERYSTRING_AUTH=True
