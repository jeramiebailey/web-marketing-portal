from django.db import models
from docker_drf_backend.users.models import User

FEEDBACK_CHOICES = (
    ('question', 'Question'),
    ('suggestion', 'Suggestion'),
    ('bug', 'Bug')
)

class UserFeedback(models.Model):
    user = models.ForeignKey(User, related_name="feedback", on_delete=models.CASCADE, null=True, blank=True)
    feedback_type = models.CharField(max_length=100, choices=FEEDBACK_CHOICES)
    feedback = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'User Feedback'
        verbose_name_plural = 'User Feedback'
        permissions = (
            ('view_userfeedback__dep', 'View User Feedback Deprecated'),
        )

    def __str__(self):
        return "{}: {}".format(self.user.name, self.feedback_type)