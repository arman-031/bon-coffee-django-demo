import os

os.environ['PYTHON_DOTENV_DISABLED'] = 'true'
os.environ.setdefault('DJANGO_SECRET_KEY', 'isolated-test-key-not-for-deployment')
os.environ['DEBUG'] = 'true'
os.environ['ALLOWED_HOSTS'] = 'localhost,127.0.0.1,testserver'
for name in ('DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT'):
    os.environ[name] = ''
os.environ['SQLITE_NAME'] = ':memory:'

from .settings import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
