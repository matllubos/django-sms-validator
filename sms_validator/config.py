from django.conf import settings

SMS_MAX_TOKEN_AGE = getattr(settings, 'MAX_SMS_TOKEN_AGE', 60 * 60)