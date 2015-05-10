from __future__ import unicode_literals

import string
import random
import logging

from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from chamber.shortcuts import get_object_or_none

from sms_operator.sender import sender

from sms_validator import config


def digit_token_generator():
    return ''.join(random.choice(string.digits) for _ in range(settings.SMS_TOKEN_LENGTH))


class SMSTokenManager(models.Manager):

    logger = logging.getLogger('django-sms-validator')

    def is_valid(self, obj, key):
        """
        Check if key is valid token for obj if is the token is deactivated
        """

        token = get_object_or_none(self.model, validating_type=ContentType.objects.get_for_model(obj),
                                   validating_id=obj.pk, is_active=True, key=key)
        if token is not None and not token.is_expired:
            token.is_active = False
            token.save()
            return True
        else:
            return False

    def count_tokens(self, obj):
        """
        Return count tokens for obj
        """

        return self.filter(validating_type=ContentType.objects.get_for_model(obj),
                           validating_id=obj.pk).count()

    def send_token(self, phone_number, obj, context, template_name='default_sms_template.html'):
        """
        Invalidate old tokens, create validation token and send key inside sms to selected phone_number
        """

        # Invalidate old tokens
        self.filter(validating_type=ContentType.objects.get_for_model(obj),
                    validating_id=obj.pk, is_active=True).update(is_active=False)

        # Create new token
        token = self.create(validating_obj=obj, phone_number=phone_number)
        context.update(
            {'key': token.key}
        )

        try:
            return not sender.send_template(phone_number, slug='token-validation', context=context).failed
        except sender.SMSSendingError:
            return False


class SMSToken(models.Model):
    """
    The SMS tokens class contains sent sms tokens to verify
    """
    key = models.CharField(verbose_name=_('token'), max_length=40, primary_key=True, null=False, blank=False)
    created_at = models.DateTimeField(verbose_name=_('created'), auto_now_add=True, null=False, blank=False)
    is_active = models.BooleanField(verbose_name=_('is active'), default=True)
    phone_number = models.CharField(verbose_name=_('phone'), max_length=20, null=False, blank=False)
    validating_type = models.ForeignKey(ContentType, verbose_name=('content type'))
    validating_id = models.PositiveIntegerField(('object ID'))
    validating_obj = generic.GenericForeignKey('validating_type', 'validating_id')

    objects = SMSTokenManager()

    def save(self, *args, **kwargs):
        if not self.key:
            key = self.generate_key()
            while SMSToken.objects.filter(key=key).exists():
                key = self.generate_key()
            self.key = key
        return super(SMSToken, self).save(*args, **kwargs)

    def generate_key(self):
        """
        Random token generating
        """
        return digit_token_generator()

    @property
    def is_expired(self):
        return self.created_at + timedelta(seconds=config.SMS_MAX_TOKEN_AGE) < timezone.now()

    def __unicode__(self):
        return self.key

    class Meta:
        verbose_name = _('SMS token')
        verbose_name_plural = _('SMS tokens')
        ordering = ('-created_at',)
