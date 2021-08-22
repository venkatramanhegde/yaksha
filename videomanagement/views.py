from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from .serializers import SignUpSerializer
from .models import User, Programs, VideoOrders, UserProgramAssociation, OtpVerification
from django.contrib.auth import authenticate, login, logout
from django.core.files.storage import FileSystemStorage
import os
from django.shortcuts import render, HttpResponseRedirect
from django.urls import reverse
import razorpay
import boto3
from django.contrib.auth.mixins import LoginRequiredMixin
from nammakalenammahemme.settings import AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_STORAGE_BUCKET_NAME, AWS_URL
from nammakalenammahemme.settings import razorpay_key, razorpay_value
from django.http import HttpResponse
import json
import math, random

# Create your views here.


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "loginpage.html")
    def post(self, request):
        print(request.POST)
        user = authenticate(email=request.POST.get('email', None).lower(),
                            password=request.POST.get('password', None))
        print(user)
        if user is not None:
            login(request, user)
            if user.is_admin:
                data = {"msg": "admin"}
                return JsonResponse(data, safe=False)
            if user.is_user:
                data = {"msg": "user"}
                return JsonResponse(data, safe=False)
        else:
            data = {"msg": "fail"}
            return JsonResponse(data, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class CreateUser(View):
    serializer_class = SignUpSerializer
    def post(self, request):
        print(request.POST)
        user = User.objects.create(name = request.POST['first_name'],
                                   email=request.POST['email'],
                                   phone_number=request.POST['phone_number']
                                   )
        user.set_password(request.POST.get('password'))
        user.save()
        programs_list = Programs.objects.all()
        for p in programs_list:
            UserProgramAssociation.objects.create(user_id=user.id,
                                                  video_id=p.id,
                                                  program_title=p.program_title,
                                                  pamphlet_path=p.image_path
                                                  )
        return JsonResponse({"msg": "user added successfully"})


@method_decorator(csrf_exempt, name='dispatch')
class ProgramUpload(View):
    def post(self, request):
        file_obj = request.FILES.get('docfile', '')
        cloud_filename = "media/programs/pamphlet/" + str(request.user.id) + '/' + file_obj.name
        video_saving_path = AWS_URL + cloud_filename
        session = boto3.session.Session(aws_access_key_id=AWS_ACCESS_KEY,
                                        aws_secret_access_key=AWS_SECRET_KEY,
                                        region_name='ap-south-1',
                                        )
        s3 = session.resource('s3')
        s3.Bucket(AWS_STORAGE_BUCKET_NAME).put_object(Key=cloud_filename, Body=file_obj, ACL="public-read")
        programs = Programs.objects.create(program_title=request.POST.get("yakshaname"),
                             uploaded_by_id=request.user.id,
                             description=request.POST.get("description"),
                             amount=request.POST.get("amount"),
                             image_path=video_saving_path
                             )
        user_list = User.objects.all()
        for user in user_list:
            UserProgramAssociation.objects.create(user_id=user.id,
                                                  video_id=programs.id,
                                                  program_title=request.POST.get("yakshaname"),
                                                  pamphlet_path = video_saving_path
                                                  )
        data = {"msg": "video uploaded successfully"}
        return JsonResponse(data, safe=False)


class UploaderPage(LoginRequiredMixin, View):
    login_url = '/videomanagement/login/'
    def get(self, request, *args, **kwargs):
        videos = Programs.objects.all()
        user_list = User.objects.filter(is_user=True)
        context = {'videos': videos, "user_list": user_list}
        return render(request, "uploader.html", context)


class UserPage(LoginRequiredMixin, View):
    login_url = '/videomanagement/login/'
    def get(self, request, *args, **kwargs):
        videos = Programs.objects.all()
        context = {'videos': videos}
        return render(request, "user.html", context)


@method_decorator(csrf_exempt, name='dispatch')
class PaymentView(LoginRequiredMixin, View):
    login_url = '/videomanagement/login/'

    def get(self, request):
        #create razorpay client
        print(request.GET)
        client = razorpay.Client(auth=(razorpay_key, razorpay_value))

        # create order
        print(request.GET.get('video_id'))
        amount = float(request.GET.get('amount')) * 100
        response_payment = client.order.create(dict(amount=amount,
                                                    currency='INR')
                                               )
        order_status = response_payment['status']
        response_payment["video_id"] = int(request.GET.get('video_id'))
        if order_status == 'created':
            videos = Programs.objects.all()
            videos_id_list = VideoOrders.objects.filter(user_id=request.user.id).values_list("video_id")
            premium_video = Programs.objects.filter(id__in=videos_id_list)
            context = {'videos': videos, "payment": response_payment,  "premium_video": premium_video,
                       "razorpay_key": razorpay_key}
            return render(request, "user.html", context)


@method_decorator(csrf_exempt, name='dispatch')
class PaymentSuccess(LoginRequiredMixin, View):
    login_url = '/videomanagement/login/'

    def post(self, request):
        response = request.POST
        print(response)
        video_order_count = VideoOrders.objects.filter(user_id=request.user.id,
                                                       video_id=request.POST.get("video_id")).count()
        print(video_order_count)
        if video_order_count == 0:
            video_total_buy = Programs.objects.filter(id=request.POST.get("video_id"))
            # video_total_buy.total_buy += 1
            for buy in video_total_buy:
                buy.total_buy = buy.total_buy + 1
                buy.save()
            video_order = VideoOrders(
                user_id=request.user.id,
                video_id=request.POST.get("video_id"),
                paid=True
            )
            video_order.save()
        videos = Programs.objects.all()
        videos_id_list = VideoOrders.objects.filter(user_id=request.user.id).values_list("video_id")
        print(videos_id_list)
        premium_video = Programs.objects.filter(id__in=videos_id_list)
        context = {'videos': videos, "premium_video": premium_video}
        print(videos, premium_video)
        return render(request, "user.html", context)


@method_decorator(csrf_exempt, name='dispatch')
class MobileUpload(View):
    def post(self, request):
        file_obj = request.FILES.get('docfile', '')
        program_id = request.POST.get("program_id")
        cloud_filename = "media/programs/videos /" + str(request.user.id) + '/' + file_obj.name
        video_saving_path = AWS_URL + cloud_filename
        print(video_saving_path)
        session = boto3.session.Session(aws_access_key_id=AWS_ACCESS_KEY,
                                        aws_secret_access_key=AWS_SECRET_KEY,
                                        region_name='ap-south-1',
                                        )
        s3 = session.resource('s3')
        s3.Bucket(AWS_STORAGE_BUCKET_NAME).put_object(Key=cloud_filename, Body=file_obj, ACL="public-read")
        Programs.objects.filter(id=program_id).update(mbl_video_path=video_saving_path)
        data = {"msg": "video uploaded successfully"}
        return JsonResponse(data, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class WebUpload(View):
    def post(self, request):
        file_obj = request.FILES.get('docfile', '')
        program_id = request.POST.get("program_id")
        cloud_filename = "media/programs/videos /" + str(request.user.id) + '/' + file_obj.name
        video_saving_path = AWS_URL + cloud_filename
        print(video_saving_path)
        session = boto3.session.Session(aws_access_key_id=AWS_ACCESS_KEY,
                                        aws_secret_access_key=AWS_SECRET_KEY,
                                        region_name='ap-south-1',
                                        )
        s3 = session.resource('s3')
        s3.Bucket(AWS_STORAGE_BUCKET_NAME).put_object(Key=cloud_filename, Body=file_obj, ACL="public-read")
        Programs.objects.filter(id=program_id).update(web_video_path=video_saving_path)
        data = {"msg": "video uploaded successfully"}
        return JsonResponse(data, safe=False)

class Logout(View):
    def get(self, request):
        logout(request)
        data = {"msg": "success"}
        return JsonResponse(data, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class VideoAccessView(View):
    def post(self, request):
        print(request.POST)
        program_list = Programs.objects.all()
        # for program in program_list:
            # UserProgramAssociation.objects.create(user_id=request.POST["user_id"],
            #                                       video_id=program.id,
            #                                       pamphlet_path=program.image_path,
            #                                       program_title=program.program_title
            #                                       )
        video_access_list = UserProgramAssociation.objects.filter(
                            user_id=request.POST["user_id"]).values("pamphlet_path",
                                                                    "video_id",
                                                                    "program_title",
                                                                    "have_access"
                                                                    )
        print(video_access_list)
        data = {"video_access_list": list(video_access_list)}
        return JsonResponse(data, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class GiveVideoAccessView(View):
    def post(self, r):
        print(r.POST["user_id"])
        video_access_update = UserProgramAssociation.objects.filter(user_id=r.POST["user_id"],
                                                                    video_id=r.POST["video_id"]).update(
                                                                    have_access=True)
        data = {"msg": "access give successfully"}
        return JsonResponse(data, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class RemoveVideoAccessView(View):
    def post(self, r):
        print(r.POST["user_id"])
        video_access_update = UserProgramAssociation.objects.filter(user_id=r.POST["user_id"],
                                                                    video_id=r.POST["video_id"]).update(
                                                                    have_access=False)
        data = {"msg": "access removed successfully"}
        return JsonResponse(data, safe=False)


class SpecialVideoListView(View):
    def get(self, request):
        video_access_list = UserProgramAssociation.objects.filter(
            user_id=request.user.id, have_access=True).values("pamphlet_path",
                                                              "video_id",
                                                              "program_title",
                                                              "have_access",
                                                              "video__web_video_path"
                                                              )
        print(video_access_list)
        data = {"video_access_list": list(video_access_list)}
        return JsonResponse(data, safe=False)




from django.core.mail import send_mail
from django.core.mail.message import EmailMessage
from nammakalenammahemme.settings import EMAIL_HOST_USER
def generateOTP():
    digits = "0123456789"
    OTP = ""
    for i in range(4):
        OTP += digits[math.floor(random.random() * 10)]
    return OTP

@method_decorator(csrf_exempt, name='dispatch')
class CheckMail(View):
    def post(self, request):
        status = True
        email = User.objects.filter(email=request.POST.get("email")).first()
        mail = request.POST.get("email")
        if hasattr(email, "email"):
            status = False
        else:
            to_email_list = [request.POST.get("email")]
            subject = "OTP Request"
            o = generateOTP()
            email_message = 'Your OTP is ' + o
            user_email = EMAIL_HOST_USER
            email = EmailMessage(subject, email_message, user_email, to=to_email_list)
            email.send()
            try:
                OtpVerification.objects.create(email=request.POST.get("email"), otp=o)
            except:
                OtpVerification.objects.filter(email=request.POST.get("email")).update(otp=o)
            status = True

        data = {"status": status}
        return JsonResponse(data, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class SendOtpEmail(View):
    def get(self, request):
        to_email_list = [request.GET.get("email")]
        subject = "OTP Request"
        o = generateOTP()
        email_message = '<p>Your OTP is <strong> ' + o + '</strong></p>'
        user_email = EMAIL_HOST_USER
        email = EmailMessage(subject, email_message, user_email, to=to_email_list)
        email.send()
        data = {"otp": o}
        return JsonResponse(data, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class OtpVerificationView(View):
    def post(self, request):
        otp = request.POST["otp"]
        email = request.POST["email"]
        otp_obj = OtpVerification.objects.filter(email=email).values_list("otp").first()
        print(otp_obj[0], otp)
        if int(otp_obj[0]) == int(otp):
            otp_verified = True
        else:
            otp_verified = False
        data = {"msg": otp_verified}
        print(data)
        return JsonResponse(data, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class PasswordGeneration(View):
    def post(self, request):
        print("sere")
        to_email_list = [request.POST.get("email")]
        print(to_email_list)
        subject = "Forgot password"
        o = generateOTP()
        email_message = 'Your OTP is ' + o
        user_email = EMAIL_HOST_USER
        email = EmailMessage(subject, email_message, user_email, to=to_email_list)
        email.send()
        user_obj = User.objects.filter(email=request.POST.get("email")).first()
        user_obj.set_password(o)
        user_obj.save()
        data = {"msg": "success"}
        return JsonResponse(data, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class DeleteProgramView(View):
    def post(self, request):
        print(request.POST["program_id"])
        program_id=request.POST["program_id"]
        program_obj = Programs.objects.get(id=program_id)
        UserProgramAssociation.objects.filter(video_id=program_id).delete()
        VideoOrders.objects.filter(video_id=program_id).delete()
        print(program_obj)
        # user_program_assc.delete()
        program_obj.delete()
        data = {"msg": "success"}
        return JsonResponse(data, safe=False)



















