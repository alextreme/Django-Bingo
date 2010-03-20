# Django settings for django bingo example-project.
import os
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('My name', 'foo@localhost'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'djangobingo.sqlite'             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

TIME_ZONE = 'Europe/Amsterdam'
LANGUAGE_CODE = 'en-us'

SITE_ID = 1
USE_I18N = True

MEDIA_URL = '/media/'
MEDIA_ROOT = '%s%s' % (BASE_PATH, MEDIA_URL)

ADMIN_MEDIA_PREFIX = '/admin_media/'
ADMIN_MEDIA_ROOT = '%s%s' % (BASE_PATH, ADMIN_MEDIA_PREFIX)

SECRET_KEY = 'MySecretKey' # Change this if you want to be secure. 
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (

)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'ping',
    'status',
    'dashboard',
    'querybuilder',
)
