from django.urls import path
from . import views
from .Project import Project_Upload,Project_checkout,market_pay
from .kyc import SubmitKYCView

urlpatterns = [

    path('',views.index,name = "index"),
    path('About/',views.About,name = "About"),
    path('market/',views.market,name = "market"),
    path('Admin/',views.Admin,name = "Admin"),
    path('tempView/<int:id>/',views.tempView,name="tempView"),
    path('login/',views.login,name = "login"),
    path('signup/',views.signup,name = "signup"),
    path("register/",views.register,name = "register"),
    path("payment_success/<str:plan>",views.payment_success,name = "payment_success"),
    path("Entry/",views.Entry,name = "Entry"),

    path('upload-project/', views.upload_project, name='upload_project'),

    path('kyc/',views.kyc,name = "kyc"),
    path('kyc/SubmitKYC/',SubmitKYCView.as_view(),name = "SubmitKYC"),
    path('BankCard/',views.BankCard,name ="BankCard"),
    path('Project_Upload/',Project_Upload,name="Project_Upload"),

    path('Project_checkout/<int:id>/',Project_checkout,name = "Project_checkout"),
    path('market_pay/',market_pay,name = "market_pay"),

    path('privacy/',views.privacy,name = "privacy"),
    path('norefund/',views.norefund,name = "norefund"),
    path('terms/',views.terms,name = "terms"),
    path('cookie/',views.cookie,name = "cookie"),
]