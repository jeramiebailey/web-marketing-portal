from datetime import datetime
from datetime import timedelta
from django.http import HttpResponse
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
import environ
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from docker_drf_backend.taskapp.celery import app
from celery import shared_task
import json
import requests
from django.conf import settings

env = environ.Env()
mailgun_domain = env('MAILGUN_DOMAIN')
SLACK_TOKEN = env('SLACK_TOKEN')
PRIMARY_SLACK_WEBHOOK_URL = env('PRIMARY_SLACK_WEBHOOK_URL')

@app.task
def send_email(
        template, 
        recipients, 
        subject, 
        context, 
        cc_addresses=None, 
        bcc_addresses=None, 
        reply_to_addresses=None, 
        meta_data=None,
        tags=None,
        track_clicks=False,
        debug=False
    ):
    if settings.DEBUG == True or debug == True:
        recipients = ['anthony@321webmarketing.com',]
    from_email = f'321 Portal <noreply@{mailgun_domain}>'
    html = render_to_string(template, context)
    cc = []
    bcc = []
    reply_to=['support@321webmarketing.com',]
    if cc_addresses:
        for address in cc_addresses:
            cc.append(address)
    if bcc_addresses:
        for address in bcc_addresses:
            bcc.append(address)
    if reply_to_addresses:
        for address in reply_to_addresses:
            reply_to.append(address)
    email = EmailMultiAlternatives(
                    subject=subject, 
                    body=html,
                    from_email=from_email, 
                    to=recipients,
                    cc=cc,
                    bcc=bcc,
                    reply_to=reply_to
                )
    email.attach_alternative(html, "text/html")
    email.metadata = meta_data
    email.tags = tags
    email.track_clicks = track_clicks
    email_response = email.send()

    return email_response


def send_test_email(template, context, subject=None):
    from_email = f'321 Portal <noreply@{mailgun_domain}>'
    recipients = ['anthony@321webmarketing.com',]
    domain = f'https://{Site.objects.get_current().domain}'
    email_context = context
    if subject:
        email_subject = f'Testing - {subject}'
    else:
        email_subject = 'Testing'

    html = render_to_string(template, context)
    email = send_mail(
                    subject=email_subject, 
                    message=html,
                    html_message=html, 
                    from_email=from_email, 
                    recipient_list=recipients
                )

def send_basic_slack_message(message, recipients=None):
    if recipients:
        recipient_list = ''
        for recipient in recipients:
            if recipient.first_name:
                recipient_output = recipient.first_name.lower()
            else:
                recipient_output = recipient
            recipient_list += f'@{recipient_output} '
        message = f'{recipient_list} {message}'

    response = requests.post(
        PRIMARY_SLACK_WEBHOOK_URL, 
        json={
            'text': message
        },
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code != 200:
        raise ValueError(f'Request to slack returned an error {response.status_code}, the response is:\n{response.text}')

    return response

def send_custom_slack_message(block_output):
    # this is an example
    block_output_example = {
        "blocks": [
            {
                'type': "section",
                "text": {
                    'type': "mrkdwn",
                    'text': "This is a test block"
                }
            }
        ]
    }
    response = requests.post(
        PRIMARY_SLACK_WEBHOOK_URL, 
        json=block_output,
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code != 200:
        raise ValueError(f'Request to slack returned an error {response.status_code}, the response is:\n{response.text}')

    return response