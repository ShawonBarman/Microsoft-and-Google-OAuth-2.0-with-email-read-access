from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = models.TextField()
    account_type = models.CharField(choices=[('google', 'Google'), ('microsoft', 'Microsoft')], max_length=20, default='google')

    def __str__(self):
        return self.user.email
