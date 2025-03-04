from django.urls import path
from . import views
from .Project import Project_Upload,Project_checkout,market_pay,get_payout_data,market_sale
from .kyc import SubmitKYCView

urlpatterns = [

    path('',views.index,name = "index"),
    path('about-us/',views.About,name = "about-us"),
    path('market/',views.market,name = "market"),
    path('Admin/',views.Admin,name = "Admin"),
    path('tempView/<int:id>/',views.tempView,name="tempView"),
    path('login/',views.login,name = "login"),
    path('signup/',views.signup,name = "signup"),
    path("register/",views.register,name = "register"),
    path("payment_success/<str:plan>",views.payment_success,name = "payment_success"),
    path("Entry/",views.Entry,name = "Entry"),
    path("UploadProfilePic/",views.UploadProfilePic,name = "UploadProfilePic"),
    path("ChangePassword/",views.ChangePassword,name = "ChangePassword"),
    path('logout/', views.logout_view, name='logout'),

    path('auth-receiver/',views.auth_receiver,name="auth-receiver"),

    path('withdraw/',views.withdraw,name = "withdraw"),


    path("GooglePlan/",views.GooglePlan,name = "GooglePlan"),
    path("Gpayment_success/<str:plan>",views.Gpayment_success,name = "Gpayment_success"),


    path('kyc/',views.kyc,name = "kyc"),
    path('kyc/SubmitKYC/',SubmitKYCView.as_view(),name = "SubmitKYC"),
    path('BankCard/',views.BankCard,name ="BankCard"),
    path('EditBankCard/',views.EditBankCard,name = "EditBankCard"),

    path('process_withdraw_request/',views.process_withdraw_request,name = "process_withdraw_request"),


    path('Project_Upload/',Project_Upload,name="Project_Upload"),

    path('Project_checkout/<int:id>/',Project_checkout,name = "Project_checkout"),
    path('market_pay/',market_pay,name = "market_pay"),
    path("get_payout_data/", get_payout_data, name="get_payout_data"),

    path("RenewPlan/",views.RenewPlan,name = "RenewPlan"),
    path("Renew_payment_success/<str:plan>",views.Renew_payment_success,name = "Renew_payment_success"),

    path('privacy/',views.privacy,name = "privacy"),
    path('norefund/',views.norefund,name = "norefund"),
    path('terms/',views.terms,name = "terms"),
    path('cookie/',views.cookie,name = "cookie"),


    path('Submail/',views.Submail,name = "Submail"),
    path('ContactMail/',views.ContactMail,name = "ContactMail"),

    

    path('market-sale/', market_sale, name='market_sale'),

    path('forget/,', views.forget, name='forget'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('change-password/', views.change_password, name='change_password'),
]