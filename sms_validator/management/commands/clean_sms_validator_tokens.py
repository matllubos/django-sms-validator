from __future__ import unicode_literals

from datetime import timedelta

from django.utils import timezone
from django.core.management.base import BaseCommand

from sms_validator.config import settings
from sms_validator.models import SMSToken


class Command(BaseCommand):

    def handle(self, **options):
        tokens_to_remove_qs = SMSToken.objects.filter(
            created_at__lt=timezone.now() - timedelta(seconds=settings.REMOVE_TOKEN_AFTER_SECONDS)
        )
        self.stdout.write('Removing {} SMS validation tokens'.format(tokens_to_remove_qs.count()))
        tokens_to_remove_qs.delete()
