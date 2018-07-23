import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# enable venv
activate_this = os.path.join(BASE_DIR, 'venv', 'bin', 'activate_this.py')
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

# add application location to system path
sys.path.append(BASE_DIR)

os.environ["DJANGO_SETTINGS_MODULE"] = "project.settings.prod"

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
