from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import UserManager
from django.contrib.postgres.fields import ArrayField


class User(AbstractBaseUser):
    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True, unique=True)
    phone_number = models.CharField(max_length=20, null=False)
    password = models.CharField(max_length=512)
    is_admin = models.BooleanField(default=False)
    is_user = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    objects = UserManager()
    USERNAME_FIELD = 'email'


class Programs(models.Model):
    program_title = models.CharField(max_length=100, null=False)
    uploaded_by = models.ForeignKey(User, null=False, on_delete=True, related_name='uploadeduser')
    uploaded_on = models.DateTimeField(auto_now=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    himmele = ArrayField(models.CharField(max_length=35), null=True)
    mummela = ArrayField(models.CharField(max_length=35), null=True)
    amount = models.FloatField(null=True)
    mbl_video_path = models.FileField(max_length=1000, null=True)
    web_video_path = models.FileField(max_length=1000, null=True)
    image_path = models.FileField(max_length=1000, null=True)
    total_buy = models.IntegerField(default=0)



class VideoOrders(models.Model):
    user = models.ForeignKey(User, null=False, on_delete=False, related_name="video_order_user")
    video = models.ForeignKey(Programs, null=False, on_delete=False, related_name="user_order_video")
    order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    paid = models.BooleanField(default=False)
