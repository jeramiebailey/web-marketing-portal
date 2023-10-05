from django.db import models
from docker_drf_backend.users.models import User

class Ticket(models.Model):
    subject = models.CharField(max_length=255)
    body = models.TextField()
    created_by = models.ForeignKey(User, related_name="user_tickets", null=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Ticket'

    def __str__(self):
        return "{}".format(self.subject)

class TicketReply(models.Model):
    ticket = models.ForeignKey(Ticket, related_name="ticket_replies", on_delete=models.CASCADE)
    body = models.TextField()
    created_by = models.ForeignKey(User, related_name="user_ticket_replies", null=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ticket Reply'

    def __str__(self):
        return "{}".format(self.ticket.id)
