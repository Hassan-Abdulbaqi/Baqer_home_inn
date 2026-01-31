"""
WSGI config for Home Inn Cafe project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'home_inn_cafe.settings')

application = get_wsgi_application()
