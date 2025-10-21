"""
ASGI config for luckyseven project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'luckyseven.settings')

application = get_asgi_application()
