import os
import sys
import site

sys.path.append(os.path.dirname(__file__))
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

site.addsitedir(os.path.join(root_dir, 'env/lib/python2.5/site-packages'))

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
