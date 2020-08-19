from __future__ import unicode_literals

import string
import random
import logging

from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from pymess.backend import sms

from sms_validator.config import settings


def digit_token_generator():
    return ''.join(random.choice(string.digits) for _ in range(settings.TOKEN_LENGTH))


class SMSTokenManager(models.Manager):

    logger = logging.getLogger('django-sms-validator')

    def get_last_active_token_or_none(self, obj, slug=None):
        """
        Returns last active or None
        """
        return self.model.objects.filter(validating_type=ContentType.objects.get_for_model(obj),
                                         validating_id=obj.pk, is_active=True, slug=slug).first()

    def get_active_token_or_none(self, obj, key, slug=None):
        """
        Returns token or None
        """

        token = self.get_last_active_token_or_none(obj, slug)

        return token if token and (key == settings.UNIVERSAL_TOKEN or key == token.key) else None

    def get_not_expired_last_active_token_or_none(self, obj, slug=None):
        """
        Returns last active token or None
        """

        token = self.get_last_active_token_or_none(obj, slug)
        return token if token is not None and not token.is_expired else None

    def get_not_expired_active_token_or_none(self, obj, key, slug=None):
        """
        Returns active token or None
        """

        token = self.get_active_token_or_none(obj, key, slug)
        return token if token is not None and not token.is_expired else None

    def is_valid(self, obj, key, slug=None):
        """
        Check if key is valid token for obj if is the token is deactivated
        """
        return self.get_not_expired_active_token_or_none(obj, key=key, slug=slug) is not None

    def deactivate_tokens(self, obj, slug=None):
        self.filter(validating_type=ContentType.objects.get_for_model(obj), is_active=True, validating_id=obj.pk,
                    slug=slug).update(is_active=False)

    def count_tokens(self, obj, slug=None):
        """
        Return count tokens for obj
        """

        return self.filter(validating_type=ContentType.objects.get_for_model(obj),
                           created_at__gte=timezone.now() - timedelta(seconds=settings.MAX_TOKEN_AGE_SECONDS),
                           validating_id=obj.pk, slug=slug).count()

    def send_token(self, phone_number, obj, slug=None, context=None, template_slug='token-validation',
                   key_generator=None):
        return self.create_and_send_token(phone_number, obj, slug, context, template_slug, key_generator)[1]

    def create_and_send_token(self, phone_number, obj, slug=None, context=None, template_slug='token-validation',
                              key_generator=None):
        """
        Invalidate old tokens, create validation token and send key inside sms to selected phone_number
        """

        context = context or {}

        # Create new token
        token = SMSToken(validating_obj=obj, phone_number=phone_number, slug=slug)
        if key_generator:
            token.generate_key(key_generator=key_generator)
        token.save()

        context.update(
            {'key': token.key}
        )

        # Invalidate old tokens
        self.filter(validating_type=ContentType.objects.get_for_model(obj),
                    validating_id=obj.pk, is_active=True).exclude(pk=token.pk).update(is_active=False)

        message = sms.send_template(phone_number, slug=template_slug, context_data=context, related_objects=(obj,))
        return token, message and not message.failed


class SMSToken(models.Model):
    """
    The SMS tokens class contains sent sms tokens to verify
    """
    key = models.CharField(verbose_name=_('token'), max_length=40, primary_key=True, null=False, blank=False)
    created_at = models.DateTimeField(verbose_name=_('created'), auto_now_add=True, null=False, blank=False)
    is_active = models.BooleanField(verbose_name=_('is active'), default=True)
    phone_number = models.CharField(verbose_name=_('phone'), max_length=20, null=False, blank=False)
    slug = models.SlugField(verbose_name=_('slug'), null=True, blank=True)
    validating_type = models.ForeignKey(ContentType, verbose_name=('content type'), on_delete=models.CASCADE)
    validating_id = models.PositiveIntegerField(('object ID'))
    validating_obj = GenericForeignKey('validating_type', 'validating_id')

    objects = SMSTokenManager()

    def save(self, *args, **kwargs):
        if not self.key:
            self.generate_key()
        return super(SMSToken, self).save(*args, **kwargs)

    def generate_key(self, key_generator=digit_token_generator):
        """
        Generates token key and sets it to `key` attribute.

        Arguments:
            key_generator: Function that generates token key, must be able to return different value for each call.

        Returns:
            Generated key.
        """
        for _ in range(1000):
            key = key_generator()
            if not SMSToken.objects.filter(key=key).exists():
                self.key = key
                return key

        raise RuntimeError('Max iterations to generate key exceeded')

    @property
    def expiration_datetime(self):
        return self.created_at + timedelta(seconds=settings.MAX_TOKEN_AGE_SECONDS)

    @property
    def is_expired(self):
        return self.created_at + timedelta(seconds=settings.MAX_TOKEN_AGE_SECONDS) < timezone.now()

    def __unicode__(self):
        return '%s (%s)' % (self.key, self.slug)

    class Meta:
        verbose_name = _('SMS token')
        verbose_name_plural = _('SMS tokens')
        ordering = ('-created_at',)
