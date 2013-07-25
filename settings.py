# Django settings for django bingo example-project.
import os
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('My name', 'foo@localhost'),
)

MANAGERS = ADMINS

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "djangobingo.sqlite",
        "PASSWORD": '',
        "HOST": '',
        "PORT": '',
    }
}
TIME_ZONE = 'Europe/Amsterdam'
LANGUAGE_CODE = 'en-us'

SITE_ID = 1
USE_I18N = True

MEDIA_URL = '/media/'
MEDIA_ROOT = '%s%s' % (BASE_PATH, MEDIA_URL)

STATIC_URL = '/static/'
STATICFILES_DIRS = (
   os.path.join(BASE_PATH, 'media/'),
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)
ADMIN_MEDIA_PREFIX = '/media/admin/'
ADMIN_MEDIA_ROOT = '%s%s' % (BASE_PATH, ADMIN_MEDIA_PREFIX)

SECRET_KEY = 'MySecretKey' # Change this if you want to be secure. 
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
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
