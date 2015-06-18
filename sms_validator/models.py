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

    def is_valid(self, obj, key, slug=None):
        """
        Check if key is valid token for obj if is the token is deactivated
        """

        token = get_object_or_none(self.model, validating_type=ContentType.objects.get_for_model(obj),
                                   validating_id=obj.pk, is_active=True, key=key, slug=slug)
        return token is not None and not token.is_expired

    def deactivate_tokens(self, obj, slug=None):
        self.filter(validating_type=ContentType.objects.get_for_model(obj), is_active=True, validating_id=obj.pk,
                    slug=slug).update(is_active=False)

    def count_tokens(self, obj, slug=None):
        """
        Return count tokens for obj
        """

        return self.filter(validating_type=ContentType.objects.get_for_model(obj),
                           created_at__gte=timezone.now() - timedelta(seconds=config.SMS_MAX_TOKEN_AGE),
                           validating_id=obj.pk, slug=slug).count()

    def last_valid_token(self, obj, slug=None):
        """
        Return last valid token for obj or None
        """

        return self.filter(validating_type=ContentType.objects.get_for_model(obj),
                           created_at__gte=timezone.now() - timedelta(seconds=config.SMS_MAX_TOKEN_AGE),
                           validating_id=obj.pk, slug=slug).order_by('-created_at').first()

    def send_token(self, phone_number, obj, slug=None, context=None, template_slug='token-validation'):
        """
        Invalidate old tokens, create validation token and send key inside sms to selected phone_number
        """

        context = context or {}

        # Invalidate old tokens
        self.filter(validating_type=ContentType.objects.get_for_model(obj),
                    validating_id=obj.pk, is_active=True).update(is_active=False)

        # Create new token
        token = self.create(validating_obj=obj, phone_number=phone_number, slug=slug)
        context.update(
            {'key': token.key}
        )

        try:
            return not sender.send_template(phone_number, slug=template_slug, context=context).failed
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
    slug = models.SlugField(verbose_name=_('slug'), null=True, blank=True)
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
    def expiration_datetime(self):
        return self.created_at + timedelta(seconds=config.SMS_MAX_TOKEN_AGE)

    @property
    def is_expired(self):
        return self.created_at + timedelta(seconds=config.SMS_MAX_TOKEN_AGE) < timezone.now()

    def __unicode__(self):
        return '%s (%s)' % (self.key, self.slug)

    class Meta:
        verbose_name = _('SMS token')
        verbose_name_plural = _('SMS tokens')
        ordering = ('-created_at',)
