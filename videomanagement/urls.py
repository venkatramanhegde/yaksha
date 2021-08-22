from django.conf.urls import url
from .views import LoginView, CreateUser, UploaderPage, ProgramUpload, UserPage, PaymentView, \
    PaymentSuccess, MobileUpload, WebUpload, Logout, VideoAccessView, GiveVideoAccessView,\
    RemoveVideoAccessView, SpecialVideoListView, CheckMail, OtpVerificationView, \
    PasswordGeneration, DeleteProgramView



urlpatterns = [

    url(r'^login/', view=LoginView.as_view(), name="login"),
    url(r'^signup/', view=CreateUser.as_view(), name="sign-up"),
    url(r'^uploader/', view=UploaderPage.as_view(), name="uploader"),
    url(r'^userpage/', view=UserPage.as_view(), name="user-page"),
    url(r'^videoupload/', view=ProgramUpload.as_view(), name="video-upload"),
    url(r'^paymentorder/', view=PaymentView.as_view(), name="payment-order"),
    url(r'^paymentsuccess/', view=PaymentSuccess.as_view(), name="payment-success"),
    url(r'^mblupload/', view=MobileUpload.as_view(), name="mobile-upload"),
    url(r'^webupload/', view=WebUpload.as_view(), name="web-upload"),
    url(r'^logout/', view=Logout.as_view(), name="logout"),
    url(r'^videoaccesslist/', view=VideoAccessView.as_view(), name="video-access-list"),
    url(r'^givevideoaccess/', view=GiveVideoAccessView.as_view(), name="give-video-access"),
    url(r'^removevideoaccess/', view=RemoveVideoAccessView.as_view(), name="remove-video-access"),
    url(r'^specialvideolist/', view=SpecialVideoListView.as_view(), name="special-video-list"),
    url(r'^ckeckmail/$', view=CheckMail.as_view(), name='ckeckmail'),
    url(r'^otpvarification/$', view=OtpVerificationView.as_view(), name='otp-varification'),
    url(r'^passwordsend/$', view=PasswordGeneration.as_view(), name='otp-passwordsend'),
    url(r'^deleteprogram/$', view=DeleteProgramView.as_view(), name='delete_program'),

]

