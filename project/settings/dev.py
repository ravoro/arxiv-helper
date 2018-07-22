from . import *

DEBUG = True
ALLOWED_HOSTS = []
SECRET_KEY = 'secret-key-placeholder'

DATABASES['default'].update({
    'USER': 'user-placeholder',
    'PASSWORD': 'password-placeholder',
})

CRONTAB_DJANGO_SETTINGS_MODULE = 'project.settings.dev'

ARXIV_FEED_URL = 'http://localhost:8000/sample-arxiv-url'
