"""Utility functions for the FOIA Application"""

from settings import DOCUMNETCLOUD_USERNAME, DOCUMENTCLOUD_PASSWORD

import base64
import json
import urllib2
from vendor import MultipartPostHandler

def make_template_choices(template_dict, level):
    """Make the data structure for the select form from the more generic data strcuture"""
    templates = [t for t in template_dict.values() if level in t.level]
    categories = set(t.category for t in templates)

    choices = []

    for category in categories:
        cat_templates = [t for t in templates if t.category == category]
        choices.append((category, [(t.slug, t) for t in cat_templates]))

    return choices

def upload_document_cloud(file_name, title, source, description, access):
    """Upload a document to Document Cloud"""

    # these need to be coerced from unicode to regular strings in order to avoid encoding errors
    file_name = str(file_name)
    title = str(title)
    source = str(source)
    description = str(description)
    access = str(access)

    username = DOCUMNETCLOUD_USERNAME
    password = DOCUMENTCLOUD_PASSWORD

    params = {
        'file': open(file_name, 'rb'),
        'title': title,
        'source': source,
        'description': description,
        'access': access,
        }

    opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler)
    request = urllib2.Request('https://www.documentcloud.org/api/upload.json', params)
    # This is just standard username/password encoding
    auth = base64.encodestring('%s:%s' % (username, password))[:-1]
    request.add_header('Authorization', 'Basic %s' % auth)

    ret = opener.open(request).read()

    return json.loads(ret)
