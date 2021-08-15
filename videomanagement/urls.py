from django.conf.urls import url
from .views import LoginView, CreateUser, UploaderPage, ProgramUpload, UserPage, PaymentView, \
    PaymentSuccess, MobileUpload, WebUpload, Logout

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

]
