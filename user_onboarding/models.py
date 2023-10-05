from django.db import models
from django.contrib.auth.models import Group
import datetime
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.sites.models import Site
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from invitations import signals
from invitations.adapters import get_invitations_adapter
from invitations.app_settings import app_settings
from invitations.base_invitation import AbstractBaseInvitation

frontend_url = settings.FRONTEND_URL 

@python_2_unicode_compatible
class CustomInvitation(AbstractBaseInvitation):
    email = models.EmailField(unique=True, verbose_name=_('e-mail address'),
                              max_length=app_settings.EMAIL_MAX_LENGTH)
    first_name = models.CharField(max_length=100, null=True)
    last_name = models.CharField(max_length=100, null=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=17, null=True, blank=True)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, blank=True, null=True)
    role = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True )
    is_writer = models.BooleanField(default=False, blank=True)
    receive_reporting_email = models.NullBooleanField(default=False, blank=True)
    receive_approval_reminders = models.NullBooleanField(default=False, blank=True)
    send_invite = models.BooleanField(default=False, blank=True)
    invite_sent = models.BooleanField(default=False, blank=True)
    create_user = models.BooleanField(default=False, blank=True)
    price = models.PositiveSmallIntegerField(null=True, default=0.00, blank=True)
    created = models.DateTimeField(verbose_name=_('created'),
                                   default=timezone.now)

    class Meta:
        unique_together = (("first_name", "last_name"))

    @classmethod
    def create(
        cls, 
        organization, 
        first_name, 
        last_name, 
        role, 
        email, 
        title=None, 
        phone_number=None, 
        is_writer=None, 
        price=None, 
        inviter=None,
        receive_reporting_email=None,
        receive_approval_reminders=None,
        send_invite=None, 
        create_user=None, 
        **kwargs
        ):
        key = get_random_string(64).lower()
        instance = cls._default_manager.create(
            email=email,
            key=key,
            inviter=inviter,
            organization=organization,
            first_name=first_name,
            last_name=last_name,
            title=title,
            phone_number=phone_number,
            role=role,
            is_writer=is_writer,
            price=price,
            receive_reporting_email=receive_reporting_email,
            receive_approval_reminders=receive_approval_reminders,
            send_invite=send_invite,
            create_user=create_user,
            **kwargs)
        return instance

    def key_expired(self):
        expiration_date = (
            self.sent + datetime.timedelta(
                days=app_settings.INVITATION_EXPIRY))
        return expiration_date <= timezone.now()

    def send_invitation(self, request, **kwargs):
        current_site = kwargs.pop('site', Site.objects.get_current())
        if self.create_user:
            invite_body = "to reset your password!"
            invite_url = "{0}/auth/request-password-reset/{1}".format(frontend_url, self.email)
            invite_url = request.build_absolute_uri(invite_url)
        else:
            invite_body = "to begin your registration!"
            invite_url = "{0}/auth/register/{1}/{2}".format(frontend_url, self.key, self.email)
            invite_url = request.build_absolute_uri(invite_url)
        ctx = kwargs
        ctx.update({
            'invite_url': invite_url,
            'invite_body': invite_body,
            'site_name': current_site.name,
            'email': self.email,
            'organization': self.organization,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'title': self.title,
            'phone_number': self.phone_number,
            'role': self.role,
            'is_writer': self.is_writer,
            'price': self.price, 
            'receive_reporting_email': self.receive_reporting_email,
            'receive_approval_reminders': self.receive_approval_reminders,
            'send_invite': self.send_invite,
            'create_user': self.create_user,
            'key': self.key,
            'inviter': self.inviter,
        })

        email_template = 'invitations/email/email_invite'

        get_invitations_adapter().send_mail(
            email_template,
            self.email,
            ctx)
        self.sent = timezone.now()
        self.save()

        signals.invite_url_sent.send(
            sender=self.__class__,
            instance=self,
            invite_url_sent=invite_url,
            inviter=self.inviter,
            organization=self.organization,
            first_name=self.first_name,
            last_name=self.last_name,
            title=self.title,
            phone_number=self.phone_number,
            role=self.role,
            is_writer=self.is_writer,
            price=self.price,
            receive_reporting_email=self.receive_reporting_email,
            receive_approval_reminders=self.receive_approval_reminders,
            send_invite=self.send_invite,
            create_user=self.create_user,
            ),

    def __str__(self):
        return "Invite: {0}".format(self.email)