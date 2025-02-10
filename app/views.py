from django.shortcuts import render,redirect
from django.contrib import messages
import re
import razorpay
from django.views.decorators.csrf import csrf_exempt
from .models import account,Project,KYCCapturedPhoto,BankDetails,ProjectFile
from netchemy.settings import RAZOR_KEY_ID,RAZOR_SECRET_ID

from google.oauth2 import id_token
from google.auth.transport import requests

from django.contrib.auth import authenticate, login
from django.utils.timezone import now
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import TokenError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from jwt import decode, ExpiredSignatureError, InvalidTokenError

from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse
import os

from django.core.mail import send_mail

client = razorpay.Client(auth=(RAZOR_KEY_ID,RAZOR_SECRET_ID))
# Create your views here.
def index(request):
   
    return render(request,'index.html')

def About(request):
    return render(request,'About.html')

def market(request):
    project = Project.objects.all()
    return render(request,'market.html',{'project':project})

def Admin(request):
    return render(request,'Admin.html')

def tempView(request,id):
    product = Project.objects.get(id = id)
    images = product.files.all()
    return render(request,'tempView.html',{'product':product,'image':images})


def login(request):
    return render(request,'login.html')

def signup(request):
    return render(request,'signup.html')

def kyc(request):
    return render(request,'Kyc.html')

def norefund(request):
    return render(request,'norefund.html')


def terms(request):
    return render(request,'terms.html')

def cookie(request):
    return render(request,'cookie.html')

def privacy(request):
    return render(request,'privacy.html')

def register(request):

    username = str(request.POST['full-name'])
    role = str(request.POST['user-role'])
    plan = str(request.POST['user-Plan'])
    nation = str(request.POST['user-nation'])
    emails = str(request.POST["email"])
    password = str(request.POST["password"])
    confirm_password = str(request.POST['Confirm_Password'])

    password_regex = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')

    if nation != "India":
        messages.error(request, 'This Feature only available in India')
        return redirect('index')

    if not password_regex.match(password):
        messages.error(request, 'Password must be at least 8 characters long and include a special character and a number.')
        return redirect('signup')

    if password != confirm_password:
        messages.error(request, 'Passwords do not match.')
        return redirect('signup')

    # Check for unique username
    if account.objects.filter(username=username).exists():
        messages.error(request, 'Username already exists. Please choose a different username.')
        return render(request, 'SignUp.html')

    # Check for unique email
    if account.objects.filter(email=emails).exists():
        messages.error(request, 'Email is already associated with an account.')
        return render(request, 'SignUp.html')
    

    price = 0
    if plan == "Pro":
        price = 249900
    if plan == "Basic":
        price = 29900
    if plan == "Creater":
        price = 849900
    
    # Razorpay order creation
    currency = 'INR'
    payment_capture = 1  
        
    order_data = {
        'amount': price,  # amount in paise
        'currency': currency,
        'payment_capture': payment_capture,
        
    }
    
    order = client.order.create(data=order_data)
    print(f"Order created: {order}")
    
    # Save email and hashed password temporarily
    request.session['UserName'] = username
    request.session['role']= role
    request.session['email'] = emails
    request.session['password'] = password
    
    ord = {
        'id': order.get('id'),
        'amount': order.get('amount'),
        'currency': order.get('currency'),
        'key_id': RAZOR_KEY_ID,
        
    }

    return render(request, 'Checkout.html', {'order':ord,'plan':plan,})


@csrf_exempt
def payment_success(request,plan):
    payment_id = request.POST['razorpay_payment_id']
    order_id = request.POST['razorpay_order_id']
    signature = request.POST['razorpay_signature']


    params_dict = {
    'razorpay_order_id': order_id,
    'razorpay_payment_id': payment_id,
    'razorpay_signature': signature
    }
    
    try:
        client.utility.verify_payment_signature(params_dict)

        # Retrieve the email and password from the session
        email = request.session.get('email')
        passwor = request.session.get('password')
        Username = request.session.get('UserName')
        Role = request.session.get('role')
        
        password = make_password(passwor)

        if plan == "Pro":
            startDate = timezone.now()
            endDate = startDate + timedelta(days=365)  # 1 year
        elif plan == "Basic":
            startDate = timezone.now()
            endDate = startDate + timedelta(days=30)  # 1 month
        elif plan == "Creater":
            startDate = timezone.now()
            endDate = timezone.datetime(2100, 1, 1, 0, 0, 0, tzinfo=timezone.utc) 


        if email and password:
            # Save the user to the database
            user = account.objects.create(username = Username,role = Role,email=email,startDate = startDate,endDate = endDate, password=password, Subscription=True,SubPlan = plan ,payment_id = params_dict['razorpay_payment_id'])

        # Optionally clear session data
        del request.session['email']
        del request.session['password']
        del request.session['UserName']
        del request.session['role']
        
        return redirect('login')
       
    except razorpay.errors.SignatureVerificationError:
        return render(request, 'SignUp.html')
   

def Entry(request):
    email = str(request.POST.get("email"))
    passw = str(request.POST.get("password"))
    
    try:
        accounts = account.objects.get(email=email)
    except account.DoesNotExist:
        messages.error(request, 'No account found with this email.')
        return redirect('login')
    
    if not check_password(passw, accounts.password):
        
        messages.error(request, 'Incorrect password.')
        return redirect('login')
        

    if accounts.Subscription:
        if accounts.endDate <=now():
            accounts.Subscription = False
            accounts.save()
            return redirect('login') 
        else:
            if accounts.SubPlan == "Creater":
                token_response = generate_jwt(accounts)
                kyc = KYCCapturedPhoto.objects.filter(kyc_id=accounts.id)

                project = Project.objects.filter(Project_id = accounts.id)

                response = render(request,"Admin.html", {
                    'username': accounts.username,
                    'access_token': token_response.data['access'],
                    'refresh_token': token_response.data['refresh'],
                    'account':accounts,
                    'KYC':kyc,
                    'project':project,
                })
                return response
            elif accounts.SubPlan == "Pro":
                token_response = generate_jwt(accounts)
                kyc = KYCCapturedPhoto.objects.filter(kyc_id=accounts.id)
                project = Project.objects.filter(Project_id = accounts.id)
                bank = BankDetails.objects.filter(bankid=accounts.id).first() 
                digits = str(bank.AccountNo)[-4:] if bank and bank.AccountNo else "N/A"

                response = render(request,"Admin.html", {
                    'username': accounts.username,
                    'access_token': token_response.data['access'],
                    'refresh_token': token_response.data['refresh'],
                    'account':accounts,
                    'KYC':kyc,
                    'project':project,
                    'digits':digits,
                    'banks':bank,
                })
                return response
            else:
                token_response = generate_jwt(accounts)
                
                response = render(request,"Admin.html", {
                    'username': accounts.username,
                    'access_token': token_response.data['access'],
                    'refresh_token': token_response.data['refresh'],
                    'account':accounts,
                    
                })
                return response
    else:
        messages.error(request, 'Subscription Expired')
        return redirect('login')

    
#token generation -JWT    
def generate_jwt(user):
    Refresh = RefreshToken.for_user(user)
    return Response({
        'refresh':str(Refresh),
        'access': str(Refresh.access_token),
    })


@csrf_exempt
def auth_receiver(request):
    token = request.POST.get('credential')

    if not token:
        messages.error(request, "Invalid request")
        return redirect('login')

    try:
        user_data = id_token.verify_oauth2_token(
            token, requests.Request(), os.environ['GOOGLE_OAUTH_CLIENT_ID']
        )
    except ValueError:
        messages.error(request, "Invalid token")
        return redirect('login')

    email = user_data.get('email')
    if not email:
        messages.error(request, 'Email not found in token')
        return redirect('login')

    accounts = account.objects.filter(email=email).first()

    if not accounts:
        return render(request, "plan.html", {'email': email})

    if accounts.Subscription and accounts.endDate <= now():
        accounts.Subscription = False
        accounts.save()
        messages.error(request, 'Subscription Expired')
        return render(request, "plan.html", {'email': email})

    return render_admin_page(request, accounts)

def render_admin_page(request, accounts):
    token_response = generate_jwt(accounts)
    kyc = KYCCapturedPhoto.objects.filter(kyc_id=accounts.id)
    project = Project.objects.filter(Project_id=accounts.id)
    bank = BankDetails.objects.filter(bankid=accounts.id).first()
    digits = str(bank.AccountNo)[-4:] if bank and bank.AccountNo else "N/A"

    return render(request, "Admin.html", {
        'username': accounts.username,
        'access_token': token_response.data['access'],
        'refresh_token': token_response.data['refresh'],
        'account': accounts,
        'KYC': kyc,
        'project': project,
        'digits': digits,
        'banks': bank,
    })


@csrf_exempt
def upload_project(request):
    if request.method == 'POST':
        project_name = request.POST.get('project_name')
        project_description = request.POST.get('project_description')
        price = request.POST.get('price')
        files = request.FILES.getlist('project_files')

        # Save the project details to the database
        project = Project.objects.create(
            name=project_name,
            description=project_description,
            price=price,
        )

        # Save the uploaded files
        for file in files:
            project.files.create(file=file)

        return JsonResponse({'message': 'Project uploaded successfully!'}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


def BankCard(request):
    if request.method == 'POST':
        account_number = request.POST.get('account-number')
        bank_name = request.POST.get('bank-name')
        ifsc = request.POST.get('ifsc')
        account_holder = request.POST.get('account-holder')
        access_token = request.POST.get('access_token')

        if access_token:
            try:
                # Decode access token
                decoded_token = UntypedToken(access_token)
                user_id = decoded_token['user_id']
                user = account.objects.get(id=user_id)

                # Save bank details
                detail = BankDetails.objects.create(
                    bankid=user,
                    AccountName= account_holder,
                    AccountNo=account_number,
                    IFSC=ifsc,
                    BankName= bank_name
                )
                detail.save()


                
                messages.success(request, "Bank details added successfully.")
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
        else:
            messages.error(request, "Access token is missing.")

    return redirect('index')




@csrf_exempt
def UploadProfilePic(request):
    if request.method == 'POST':
        images = request.FILES.get('ProfilePic')
        access_token = request.POST.get('access_token')

        if not access_token:
            return JsonResponse({'error': 'Access token is missing.'}, status=400)

        
        try:
            # Decode access token
            decoded_token = UntypedToken(access_token)
            user_id = decoded_token.get('user_id')
            if not user_id:
                return JsonResponse({'error': 'Invalid access token.'}, status=401)

            # Get the user
            user = account.objects.get(id=user_id)  # Replace `account` with your user model
            user.ProfileImg = images
            user.save()

            return JsonResponse({'success': 'Profile image uploaded successfully.'}, status=200)
        except TokenError:
            return JsonResponse({'error': 'Invalid or expired access token.'}, status=401)
        except account.DoesNotExist:
            return JsonResponse({'error': 'User not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=405)
    

def ChangePassword(request):
    if request.method == 'POST':
        CurrentPassword = request.POST.get('current-password')
        NewPassword = request.POST.get('new-password')
        NewConfirmPassword = request.POST.get('confirm-new-password')
        access_token = request.POST.get('access_token')

        if not access_token:
            return JsonResponse({'error': 'Access token is missing.'}, status=400)

        if NewPassword != NewConfirmPassword:
            return JsonResponse({'error': "New passwords do not match."}, status=400)

        try:
 
            decoded_token = decode(access_token, options={"verify_exp": False})  
            user_id = decoded_token.get('user_id')

            if not user_id:
                return JsonResponse({'error': 'Invalid access token.'}, status=401)

            user = account.objects.get(id=user_id)

  
            if not check_password(CurrentPassword, user.password):
                return JsonResponse({'error': "Invalid current password."}, status=401)


            user.password = make_password(NewPassword)
            user.save()

            return JsonResponse({'success': 'Password changed successfully.'}, status=200)

        except ExpiredSignatureError:
            return JsonResponse({'error': 'Access token has expired.'}, status=401)
        except InvalidTokenError:
            return JsonResponse({'error': 'Invalid access token.'}, status=401)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


def Submail(request):
    try:
        subject = "Subcription"
       
        email = str(request.POST['email'])

        msgs = f"Email: {email}\n"

        recipient_list = ['kirankumarr1901@gmail.com'] 
      
        send_mail(subject, msgs, 'kirankumarr1901@gmail.com',recipient_list, fail_silently=False)
        

        return JsonResponse({'success': 'Thanks for reaching out. Well respond within the day.'})
    except Exception as e:
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


def ContactMail(request):
    try:
        subject = str(request.POST['subject'])
        name = str(request.POST['name'])
        email = str(request.POST['email'])
        msg = str(request.POST['message'])
        msgs = f"Name: {name}\nEmail: {email}\n\nMessage: {msg}"

        recipient_list = ['kirankumarr1901@gmail.com'] # List of recipient email addresses
        send_mail(subject, msgs, 'kirankumarr1901@gmail.com',recipient_list, fail_silently=False)
        

        return JsonResponse({'success': 'Thanks for reaching out. Well respond within the day.'})
    except Exception as e:
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)
    


def GooglePlan(request):
    plan = request.GET.get('plan')
    user_email = request.GET.get('email')

    
    price = 0
    if plan == "Pro":
        price = 249900
    if plan == "Basic":
        price = 29900
    if plan == "Creater":
        price = 849900
    
    # Razorpay order creation
    currency = 'INR'
    payment_capture = 1  
        
    order_data = {
        'amount': price,  # amount in paise
        'currency': currency,
        'payment_capture': payment_capture,
        
    }
    
    order = client.order.create(data=order_data)
    print(f"Order created: {order}")
    
    # Save email and hashed password temporarily
    request.session['email'] = user_email
 
    
    ord = {
        'id': order.get('id'),
        'amount': order.get('amount'),
        'currency': order.get('currency'),
        'key_id': RAZOR_KEY_ID,
        
    }

    return render(request, 'GCheckout.html', {'order':ord,'plan':plan,})



@csrf_exempt
def Gpayment_success(request,plan):
    payment_id = request.POST['razorpay_payment_id']
    order_id = request.POST['razorpay_order_id']
    signature = request.POST['razorpay_signature']


    params_dict = {
    'razorpay_order_id': order_id,
    'razorpay_payment_id': payment_id,
    'razorpay_signature': signature
    }
    
    try:
        client.utility.verify_payment_signature(params_dict)

        # Retrieve the email and password from the session
        email = request.session.get('email')
     
        
        if plan == "Pro":
            startDate = timezone.now()
            endDate = startDate + timedelta(days=365)  # 1 year
        elif plan == "Basic":
            startDate = timezone.now()
            endDate = startDate + timedelta(days=30)  # 1 month
        elif plan == "Creater":
            startDate = timezone.now()
            endDate = datetime.max

        if email:
            user = account.objects.create(email=email,startDate = startDate,endDate = endDate,Subscription=True,SubPlan = plan ,payment_id = params_dict['razorpay_payment_id'])

        # Optionally clear session data
        del request.session['email']
  
        
        return redirect('login')
       
    except razorpay.errors.SignatureVerificationError:
        return render(request, 'SignUp.html')