from . import *

DEBUG = True
ALLOWED_HOSTS = []
SECRET_KEY = 'secret-key-placeholder'

DATABASES['default'].update({
    'USER': 'user-placeholder',
    'PASSWORD': 'password-placeholder',
})

INTERNAL_IPS = ['127.0.0.1']

CRONTAB_DJANGO_SETTINGS_MODULE = 'project.settings.dev'

ARXIV_DOWNLOAD_DELAY_SECONDS = 0

ARXIV_CS_FEED_URL = 'http://localhost:8000/list/cs/new/'
ARXIV_EESS_FEED_URL = 'http://localhost:8000/list/eess/new/'
ARXIV_NLIN_FEED_URL = 'http://localhost:8000/list/nlin/new/'
ARXIV_PHYSICS_FEED_URL = 'http://localhost:8000/list/physics/new/'
ARXIV_QBIO_FEED_URL = 'http://localhost:8000/list/q-bio/new/'
