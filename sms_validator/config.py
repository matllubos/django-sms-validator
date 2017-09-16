from django.conf import settings as django_settings


DEFAULTS = {
    'MAX_TOKEN_AGE_SECONDS': 60 * 60,  # 1 h
    'REMOVE_TOKEN_AFTER_SECONDS': 60 * 60 * 24 * 30,  # 30 days
    'TOKEN_LENGTH': 6,  # 6 chars
    'UNIVERSAL_TOKEN': None,
}


class Settings(object):

    def __getattr__(self, attr):
        if attr not in DEFAULTS:
            raise AttributeError('Invalid SMS validator setting: "{}"'.format(attr))

        return getattr(django_settings, 'SMS_VALIDATOR_{}'.format(attr), DEFAULTS[attr])


settings = Settings()
