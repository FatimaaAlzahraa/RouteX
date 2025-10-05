"""
WSGI config for project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os, sys

from django.core.wsgi import get_wsgi_application

project_path = "/home/zahraaayop/RouteX"
if project_path not in sys.path:
    sys.path.append(project_path)



os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RouteX.settings')

application = get_wsgi_application()
