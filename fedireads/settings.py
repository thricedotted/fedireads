''' fedireads settings and configuration '''
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '7(2w1sedok=aznpq)ta1mc4i%4h=xx@hxwx*o57ctsuml0x%fr'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# TODO: this should be populated at runtime at least for debug mode
DOMAIN = 'af064ab4.ngrok.io'
ALLOWED_HOSTS = ['*']
OL_URL = 'https://openlibrary.org'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'fedireads',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'fedireads.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'fedireads.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

# possible database configurations.
# using a leading double underscore "__" to denote that these are *not* Django config vars.
# TODO: break non-Django config vars out into a separate module? 
__DATABASE_CONFIGS = {
    'sqlite': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'fedireads.db')
    },

    'postgres': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'fedireads',
        'USER': 'fedireads',
        'PASSWORD': 'fedireads',
        'HOST': '',
        'PORT': 5432
    }
}

# read DB backend from .env, default to postgres
# TODO: raise error if DB not in DATABASE_CONFIGS
__DATABASE_BACKEND = os.getenv('DATABASE_BACKEND', 'postgres')

DATABASES = {
    'default': __DATABASE_CONFIGS[__DATABASE_BACKEND]
}

LOGIN_URL = '/login/'
AUTH_USER_MODEL = 'fedireads.User'

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/images/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'images/')
