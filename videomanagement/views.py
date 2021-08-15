from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from .serializers import SignUpSerializer
from .models import User, Programs, VideoOrders
from django.contrib.auth import authenticate, login, logout
from django.core.files.storage import FileSystemStorage
import os
from django.shortcuts import render, HttpResponseRedirect
from django.urls import reverse
import razorpay
import boto3
from django.contrib.auth.mixins import LoginRequiredMixin
from nammakalenammahemme.settings import AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_STORAGE_BUCKET_NAME, AWS_URL

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
        # user_add = self.serializer_class(data=request.POST)
        # if user_add.is_valid():
        #     user_add.save()
        #     return JsonResponse({"msg": "user added successfully"}, status=status.HTTP_201_CREATED)
        # else:
        #     return JsonResponse({"msg": user_add.errors}, status=status.HTTP_400_BAD_REQUEST)
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
        Programs.objects.create(program_title=request.POST.get("yakshaname"),
                             uploaded_by_id=request.user.id,
                             description=request.POST.get("description"),
                             amount=request.POST.get("amount"),
                             image_path=video_saving_path
                             )
        data = {"msg": "video uploaded successfully"}
        return JsonResponse(data, safe=False)




class UploaderPage(LoginRequiredMixin, View):
    login_url = '/videomanagement/login/'
    def get(self, request, *args, **kwargs):
        videos = Programs.objects.all()
        context = {'videos': videos}
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
        client = razorpay.Client(auth=('rzp_test_rtYqPGP7pemH2e', '5kuleWwB31SU8yPQbTTKN88b'))

        # create order
        print(request.GET.get('video_id'))
        amount = float(request.GET.get('amount')) * 100
        response_payment = client.order.create(dict(amount=amount,
                                                    currency='INR')
                                               )
        print(response_payment)
        order_status = response_payment['status']
        response_payment["video_id"] = int(request.GET.get('video_id'))
        if order_status == 'created':
            videos = Programs.objects.all()
            videos_id_list = VideoOrders.objects.filter(user_id=request.user.id).values_list("video_id")
            premium_video = Programs.objects.filter(id__in=videos_id_list)
            context = {'videos': videos, "payment": response_payment,  "premium_video": premium_video}
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
        session = boto3.session.Session(aws_access_key_id=AWS_ACCESS_KEY,
                                        aws_secret_access_key=AWS_SECRET_KEY,
                                        region_name='ap-south-1',
                                        )
        s3 = session.resource('s3')
        s3.Bucket(AWS_STORAGE_BUCKET_NAME).put_object(Key=cloud_filename, Body=file_obj, ACL="public-read")
        # for video in videos:
        #     videoname = str(video.name).replace(" ", "")
        #     extension = videoname.split('.')
        #     fs = FileSystemStorage(location=folder)  # defaults to DATASTORE
        #     name = fs.save(videoname, video)
        #     mediapath = folder + "{}"
        #     filepath = os.path.join(mediapath).format(name)
        #     print(filepath)
        video = Programs.objects.filter(id=program_id).update(web_video_path=video_saving_path)
        data = {"msg": "video uploaded successfully"}
        return JsonResponse(data, safe=False)

class Logout(View):
    def get(self, request):
        logout(request)
        data = {"msg": "success"}
        return JsonResponse(data, safe=False)


















