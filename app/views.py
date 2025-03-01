from django.shortcuts import render,redirect
from django.contrib import messages
import re
import razorpay
from django.views.decorators.csrf import csrf_exempt
from .models import account,Project,KYCCapturedPhoto,BankDetails,ProjectFile,Payouts,sales,WithdrawRequest,ProjectRevenue, PasswordResetOTP
from netchemy.settings import RAZOR_KEY_ID,RAZOR_SECRET_ID
from django.db.models import Sum
from google.oauth2 import id_token
from google.auth.transport import requests
from django.contrib.auth import update_session_auth_hash
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
from django.db.models import OuterRef, Subquery
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse
import os
from django.core.paginator import Paginator
from django.core.mail import send_mail
import uuid
import json
import os
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from decimal import Decimal
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
import requests
from django.utils.crypto import get_random_string
client = razorpay.Client(auth=(RAZOR_KEY_ID,RAZOR_SECRET_ID))
API_KEY = RAZOR_KEY_ID
API_SECRET = RAZOR_SECRET_ID
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

    password_regex = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!#%*?&]{8,}$')

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
        price = 499900
    
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
            endDate = datetime.max


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
            messages.error(request, 'Subscription Expired')
            return render(request,'renew.html',{'account':accounts.id}) 
        else:
            token_response = generate_jwt(accounts)

            kyc = KYCCapturedPhoto.objects.filter(kyc_id=accounts.id)
            project = Project.objects.filter(Project_id = accounts.id)
            bank = BankDetails.objects.filter(bankid=accounts.id).first() 
            digits = str(bank.AccountNo)[-4:] if bank and bank.AccountNo else "N/A"
            total_amount = Payouts.objects.filter(PayoutBankID=accounts.id).aggregate(Sum('PaidAmount'))['PaidAmount__sum']
            total_amount = float(total_amount) if total_amount else 0.0 

            payouts_list = Payouts.objects.filter(PayoutBankID__bankid=accounts.id).select_related('ProductId__SaleId__Project_id')
 
            Transactions_list = WithdrawRequest.objects.filter(WithdrawID=accounts.id)
            paginator = Paginator(Transactions_list, 10)  
            page_number = request.GET.get('page')
            Transactions = paginator.get_page(page_number)

            bank_details_subquery = BankDetails.objects.filter(
            bankid=OuterRef('WithdrawID')
            ).values('LinkId')[:1]  # Ensuring we get only one result per account

            # Fetch all WithdrawRequests with BankDetails.LinkId
            Transactions_list2 = WithdrawRequest.objects.annotate(LinkId=Subquery(bank_details_subquery)).filter(Status='on_process')

            paginator2 = Paginator(Transactions_list2, 10)  
            page_number2 = request.GET.get('page')
            Transactions2 = paginator2.get_page(page_number2)
             
            total_listings = Project.objects.filter(Project_id=accounts.id).count()
            total_purchases = sales.objects.filter(SaleId__Project_id=accounts.id).count()
            #total_revenue = sum(sale.SaleId.price for sale in sales.objects.filter(SaleId__Project_id=accounts.id))
            projects = Project.objects.filter(Project_id=accounts.id)
            total_revenue = ProjectRevenue.objects.filter(project__in=projects).aggregate(Sum('total_revenue'))['total_revenue__sum'] or 0.00

           

            context = { 
                'username': accounts.username,
                'access_token': token_response.data['access'],
                'refresh_token': token_response.data['refresh'],
                'account':accounts,
                'KYC':kyc,
                'project':project,
                'digits':digits,
                'banks':bank,
                'total_amount':total_amount,
                'transactions': Transactions,
                'transactions2': Transactions2,
                "total_listings": total_listings,
                "total_purchases": total_purchases,
                "total_revenue": total_revenue,
            }
            if email == "Test@gmail.com" and passw == "Astro@1901":
                return render(request, "Admin2.html", context)

            return render(request, "Admin.html", context)
          
    else:
        messages.error(request, 'Subscription Expired')
        return redirect('login')

    
def generate_jwt(user):
    plan_lifetimes = {
        "Pro": timedelta(days=365), 
        "Basic": timedelta(days=30),
        "Creater": timedelta(days=365 * 100),  
    }


    access_lifetime = plan_lifetimes.get(user.SubPlan)
    
    if not access_lifetime:
        return None 

    refresh = RefreshToken.for_user(user)
    refresh.access_token.set_exp(lifetime=access_lifetime)

    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    })


@csrf_exempt
def logout_view(request):
    if request.method == 'POST':
        response = JsonResponse({"message": "You have been logged out successfully!", "redirect_url": "/"})
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response
    return JsonResponse({"error": "Invalid request"}, status=400)


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





def create_linked_account(user_email, account_holder,mobile_number, bank_name, account_number):

    url = "https://api.razorpay.com/v2/accounts"

    reference_id = str(uuid.uuid4())[:20]

    linked_account_payload = {
        "email": user_email,
        "phone": mobile_number,
        "type": "route",
        "reference_id": reference_id ,
        "legal_business_name": "Trekato",
        "business_type": "partnership",
        "contact_name": account_holder,
        "profile": {
            "category": "healthcare",
            "subcategory": "clinic",
            "addresses": {
                "registered": {
                    "street1": "507, Koramangala 1st block",
                    "street2": "MG Road",
                    "city": "Bengaluru",
                    "state": "KARNATAKA",
                    "postal_code": "560034",
                    "country": "IN"
                }
            }
        },
          "legal_info": {
            "pan": "AAACL1234C",
            "gst": "18AABCU9603R1ZM"
        }
    }
    try:
        response = requests.post(
            url,
            auth=(API_KEY, API_SECRET),
            headers={"Content-Type": "application/json"},
            data=json.dumps(linked_account_payload)
        )

        if response.status_code == 200 or response.status_code == 201:
            account_data = response.json()
            account_id = account_data.get("id")
            print("Linked Account Created Successfully:", account_data)
            return account_id       
        else:
            print(f"Error Creating Linked Account: {response.status_code}, Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def create_stakeholder(account_id, account_holder, user_email):
    """Create a stakeholder for the linked account."""
    reference_id = str(uuid.uuid4())[:20]
    stakeholder_payload = {
        "name": account_holder,
        "email": user_email,
        "addresses": {
            "residential": {
                "street": "506, Koramangala 1st block",
                "city": "Bengaluru",
                "state": "Karnataka",
                "postal_code": "560034",
                "country": "IN"
            }
        },
        "kyc": {
            "pan": "AAACL1234C"  # Replace with user input
        },
        "notes": {
            "random_key_by_partner": reference_id
        }
    }

    try:
        response = client.stakeholder.create(account_id, stakeholder_payload)
        return response.get("id")
    except razorpay.errors.BadRequestError:
        return None

def request_product_configuration(account_id):
    """Request product configuration for the linked account."""
    try:
        response = client.product.requestProductConfiguration(account_id, {
            "product_name": "route",
            "tnc_accepted": True
        })
        return response.get("id")
    except razorpay.errors.BadRequestError:
        return None

def update_product_configuration(account_id, product_id, account_number, ifsc, account_holder):
    """Update the product configuration with bank details."""
    try:
        response = client.product.edit(account_id, product_id, {
            "settlements": {
                "account_number": account_number,
                "ifsc_code": ifsc,
                "beneficiary_name": account_holder
            },
            "tnc_accepted": True
        })
        return response
    except razorpay.errors.BadRequestError:
        return None

def BankCard(request):
    if request.method == 'POST':
        account_number = request.POST.get('account-number')
        bank_name = request.POST.get('bank-name')
        ifsc = request.POST.get('ifsc')
        account_holder = request.POST.get('account-holder')
        mobile_number =int( request.POST.get('mobile-number'))
        access_token = request.POST.get('access_token')
        if access_token:
            try:
                # Decode access token
                decoded_token = UntypedToken(access_token)
                user_id = decoded_token['user_id']
                user = account.objects.get(id=user_id)

                # Fetch email from user model
                user_email = user.email  

                # Create Razorpay linked account
                account_id = create_linked_account(user_email ,account_holder,mobile_number, bank_name, account_number)
                if not account_id:
                    messages.error(request, "Failed to create Razorpay linked account.")
                    

                # Create stakeholder
                stakeholder_id = create_stakeholder(account_id, account_holder, user_email)
                if not stakeholder_id:
                    messages.error(request, "Failed to create stakeholder.")
                   
                # Request product configuration
                product_id = request_product_configuration(account_id)
                if not product_id:
                    messages.error(request, "Failed to request product configuration.")
                  

                # Update product configuration with bank details
                if not update_product_configuration(account_id, product_id, account_number, ifsc, account_holder):
                    messages.error(request, "Failed to update product configuration.")
                  
                # Save bank details in Django model with LinkId
                detail = BankDetails.objects.create(
                    bankid=user,
                    LinkId=account_id,  # Store the linked account ID
                    AccountName=account_holder,
                    MobileNumber = mobile_number,
                    AccountNo=account_number,
                    IFSC=ifsc,
                    BankName=bank_name
                )
                detail.save()

                messages.success(request, "Bank details added and Razorpay account created successfully.")
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
        else:
            messages.error(request, "Access token is missing.")

    return redirect(request.META.get('HTTP_REFERER', 'default_url'))



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
            messages.error(request, 'Access token is missing.')
            return redirect('Entry')  # Stay on the same page

        if NewPassword != NewConfirmPassword:
            messages.error(request, "New passwords do not match.")
            return redirect('Entry')

        try:
            decoded_token = UntypedToken(access_token)
            user_id = decoded_token.get('user_id')

            if not user_id:
                messages.error(request, 'Invalid access token.')
                return redirect('Entry')

            user = account.objects.get(id=user_id)

            if not check_password(CurrentPassword, user.password):
                messages.error(request, "Invalid current password.")
                return redirect('Entry')

            user.password = make_password(NewPassword)
            user.save()

            # Keep the user logged in
            update_session_auth_hash(request, user)

            messages.success(request, 'Password changed successfully.')
            return redirect('Entry')

        except ExpiredSignatureError:
            messages.error(request, 'Access token has expired.')
            return redirect('Entry')
        except InvalidTokenError:
            messages.error(request, 'Invalid access token.')
            return redirect('Entry')
        except account.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('Entry')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('Entry')
        

def Submail(request):
    try:
        subject = "Subcription"
       
        email = str(request.POST['email'])

        msgs = f"Email: {email}\n"

        recipient_list = ['support@snippat.com'] 
      
        send_mail(subject, msgs, 'snippat.service@gmail.com',recipient_list, fail_silently=False)
        
        messages.info(request, 'Thanks for Subscribing. Welcome to Snippat')
        return  redirect('index')
    except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('index')


def ContactMail(request):
    try:
        subject = str(request.POST['subject'])
        name = str(request.POST['name'])
        email = str(request.POST['email'])
        phone = str(request.POST['Phone'])
        msg = str(request.POST['message'])
        msgs = f"Name: {name}\nEmail: {email}\nPhone:{phone}\n\nMessage: {msg}"

        recipient_list = ['support@snippat.com'] # List of recipient email addresses
        send_mail(subject, msgs, 'snippat.service@gmail.com',recipient_list, fail_silently=False)
        
        messages.info(request, 'Thanks for reaching out. We will respond within the day.')
        return  redirect('index')
    except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('index')
        
    


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
    

    

def RenewPlan(request):
    plan = request.GET.get('plan')
    user_email = request.GET.get('id')
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
    request.session['id'] = user_email
 
    
    ord = {
        'id': order.get('id'),
        'amount': order.get('amount'),
        'currency': order.get('currency'),
        'key_id': RAZOR_KEY_ID,
        
    }

    return render(request, 'renewCheckout.html', {'order':ord,'plan':plan,})



@csrf_exempt
def Renew_payment_success(request,plan):
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
        user_id = request.session.get('id')
     
        
        if plan == "Pro":
            startDate = timezone.now()
            endDate = startDate + timedelta(days=365)  # 1 year
        elif plan == "Basic":
            startDate = timezone.now()
            endDate = startDate + timedelta(days=30)  # 1 month
        elif plan == "Creater":
            startDate = timezone.now()
            endDate = datetime.max

        if id:
            accounts = account.objects.filter(id=user_id).first()
            if accounts:
                accounts.Subscription = True
                accounts.startDate = startDate
                accounts.SubPlan = plan
                accounts.endDate = endDate
                accounts.save() 


        # Optionally clear session data
        del request.session['email']
  
        
        return redirect('login')
       
    except razorpay.errors.SignatureVerificationError:
        return render(request, 'SignUp.html')
    

@csrf_exempt
def withdraw(request):
    if request.method == "POST":
        access_token = request.headers.get("Authorization", "").split(" ")[-1]
        try:
            decoded_token = UntypedToken(access_token)
            user_id = decoded_token["user_id"]
            user = account.objects.get(id=user_id)
            data = json.loads(request.body)
            amount = float(data.get("amount", 0))

            requests = WithdrawRequest.objects.create(WithdrawID=user, Amount=amount)
            requests.save()
            return JsonResponse({"message": "Withdraw request submitted successfully."}, status=200)
        except Exception as e:
            return JsonResponse({"message": f"An error occurred: {str(e)}"}, status=500)
    return JsonResponse({"message": "Invalid request."}, status=400)

def process_withdraw_request(request):
    if request.method == "POST":
        withdraw_id = request.POST.get('transaction_id')
        action = request.POST.get('action')

        try:
            withdraw_request = WithdrawRequest.objects.get(id=withdraw_id)
            user = withdraw_request.WithdrawID

            if action == "done":
                withdraw_request.Status = "done"
                withdraw_request.save()

                project_revenue = ProjectRevenue.objects.filter(project__Project_id=user).first()
                if project_revenue:
                    project_revenue.total_revenue -= Decimal(str(withdraw_request.Amount))
                    project_revenue.save()

                # Send success email
                subject = "Withdrawal Request Processed Successfully"
                message = f"""
                Dear {user.username},

                We are pleased to inform you that your withdrawal request has been successfully processed. Below are the details of your transaction:

                Withdrawal Request ID: {withdraw_request.id}
                Amount: ₹{withdraw_request.Amount}
                Status: {withdraw_request.get_Status_display()}
                Date: {withdraw_request.Date.strftime('%Y-%m-%d %H:%M:%S')}

                If you have any questions or need further assistance, please feel free to contact our support team.

                Best regards,
                The Snippat Team
                """
                send_mail(subject, message, 'snippat.service@gmail.com', [user.email], fail_silently=False)

                messages.success(request, "Withdraw request processed successfully.")
            elif action == "cancel":
                withdraw_request.Status = "cancel"
                withdraw_request.save()

                messages.success(request, "Withdraw request cancelled successfully.")
            else:
                messages.error(request, "Invalid action.")
        except WithdrawRequest.DoesNotExist:
            messages.error(request, "Withdraw request not found.")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")

    return redirect(request.META.get('HTTP_REFERER', 'default_url'))

def EditBankCard(request):
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

                # Fetch existing bank details
                bank_details = BankDetails.objects.get(bankid=user)
                account_id = bank_details.LinkId

                # Request product configuration
                product_id = request_product_configuration(account_id)
                if not product_id:
                    messages.error(request, "Failed to request product configuration.")
                    return redirect(request.META.get('HTTP_REFERER', 'default_url'))

                # Update product configuration with bank details
                if not update_product_configuration(account_id, product_id, account_number, ifsc, account_holder):
                    messages.error(request, "Failed to update product configuration.")
                    return redirect(request.META.get('HTTP_REFERER', 'default_url'))

                # Update bank details in Django model
                bank_details.AccountName = account_holder
                bank_details.AccountNo = account_number
             
                bank_details.IFSC = ifsc
                bank_details.BankName = bank_name
                bank_details.save()

                messages.success(request, "Bank details updated successfully.")
            except BankDetails.DoesNotExist:
                messages.error(request, "Bank details not found.")
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
        else:
            messages.error(request, "Access token is missing.")

    return redirect(request.META.get('HTTP_REFERER', 'default_url'))
def forget(request):
    return render(request,'forgot_password.html')

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = account.objects.get(email=email)
            otp = get_random_string(length=6, allowed_chars='0123456789')
            PasswordResetOTP.objects.create(user=user, otp=otp, created_at=timezone.now())

            # Send OTP email
            subject = "Password Reset OTP"
            message = f"Your OTP for password reset is: {otp}"
            send_mail(subject, message, 'snippat.service@gmail.com', [email], fail_silently=False)

            messages.success(request, "OTP has been sent to your email.")
            return redirect('verify_otp')
        except account.DoesNotExist:
            messages.error(request, "No account found with this email.")
    return render(request, 'forgot_password.html')

def verify_otp(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        otp = request.POST.get('otp')
        try:
            user = account.objects.get(email=email)
            otp_record = PasswordResetOTP.objects.filter(user=user, otp=otp, created_at__gte=timezone.now() - timedelta(minutes=10)).first()
            if otp_record:
                otp_record.delete()
                request.session['reset_email'] = email
                return redirect('change_password')
            else:
                messages.error(request, "Invalid or expired OTP.")
        except account.DoesNotExist:
            messages.error(request, "No account found with this email.")
    return render(request, 'verify_otp.html')

def change_password(request):
    if request.method == 'POST':
        email = request.session.get('reset_email')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('change_password')

        try:
            user = account.objects.get(email=email)
            user.password = make_password(new_password)
            user.save()
            del request.session['reset_email']
            messages.success(request, "Password changed successfully.")
            return redirect('login')
        except account.DoesNotExist:
            messages.error(request, "No account found with this email.")
    return render(request, 'change_password.html')