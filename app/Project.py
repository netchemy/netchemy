from django.shortcuts import render,redirect
from django.contrib import messages
import re
import razorpay
from django.views.decorators.csrf import csrf_exempt
from .models import account,Project,KYCCapturedPhoto,BankDetails,ProjectFile,sales,Payouts,WithdrawRequest,ProjectRevenue
from netchemy.settings import RAZOR_KEY_ID,RAZOR_SECRET_ID

from google.oauth2 import id_token
from google.auth.transport import requests

from django.contrib.auth import authenticate, login
from django.utils.timezone import now
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import UntypedToken

from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse
import os
import json

from django.core.mail import send_mail


client = razorpay.Client(auth=(RAZOR_KEY_ID,RAZOR_SECRET_ID))

def Project_Upload(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        sell_dis = request.POST.get('description')
        whats_included = request.POST.get('whats-included')
        price = request.POST.get('price', 0)
        currency = request.POST.get('currency')
        preview_link = request.POST.get('preview')
        drive_link = request.POST.get('drive_link')
        preview_image = request.FILES.get('images')
        project_file = request.FILES.get('project_file')
        images = request.FILES.getlist('images')

        access_token = request.POST.get('access_token')

        if access_token:
            try:
                # Decode access token
                decoded_token = UntypedToken(access_token)
                user_id = decoded_token['user_id']
                user = account.objects.get(id=user_id)

                 # Check KYC verification
                kyc = KYCCapturedPhoto.objects.filter(kyc_id=user, verified=True).first()
                if not kyc:
                    messages.error(request, f"KYC not verified. Complete KYC to upload a sell entry.")
                    return redirect('index')

                # Check Bank Details
                bank_details_exist = BankDetails.objects.filter(bankid=user).exists()
                if not bank_details_exist:
                    messages.error(request, f"Bank details missing. Add bank details to upload a sell entry.")
                    return redirect('index')
                # Enforce Upload Limits
                plan = user.SubPlan
                current_month_start = now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                project_count = Project.objects.filter(Project_id=user, uploaded_at=current_month_start).count()

                # Define upload limits
                limits = {
                    "Basic": 2,
                    "Pro": 5,
                    "Creater": float('inf')  
                }

                max_uploads = limits.get(plan, 0)  

                if project_count >= max_uploads:
                    messages.error(request, f"Upload limit reached for {plan} plan. Upgrade your plan for more uploads.")
                    return redirect('index')
                
                
                # Save the main Sell object
                sell = Project.objects.create(
                    Project_id=user,
                    Title=title,
                    ProjectDis=sell_dis,
                    includes=whats_included,
                    price=price,
                    currency=currency,
                    PriviewLink=preview_link,
                    drive_link=drive_link,
                    PreviewImage=preview_image,
                    project_file=project_file,
                )

                # Save multiple images
                for image in images:
                    img = ProjectFile.objects.create(project=sell, file=image)
                img.save()
                sell.save()

                messages.success(request, "Project Listed successfully.")
                return redirect('market')
            except account.DoesNotExist:
                messages.error(request, f"User not found")
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
    return redirect('index')


def Project_checkout(request,id):
    try:
        product = Project.objects.get(id= id) 
        payment_capture = 1  
        order_data = {
            'amount': float(product.price) * 100, 
            'currency': 'INR',
            'payment_capture': payment_capture,
        }


        order = client.order.create(data=order_data)
        print(f"Order created: {order}")

        request.session['product'] = product.id
    
        ord = {
            'id': order.get('id'),
            'amount': order.get('amount'),
            'currency': order.get('currency'),
            'key_id': RAZOR_KEY_ID,
            
        }

        return render(request,"Project_checkout.html",{'product': product,'order':ord})

    except Exception as e:
     
        print(f"Error: {e}")
        return JsonResponse({"error": "An error occurred while processing your request."}, status=500)

@csrf_exempt
def market_pay(request):
   
    if request.method == 'POST':
        data = json.loads(request.body)
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')


        email = data.get("email")
        address_line1 = data.get("address_line1")
        country = data.get("country")
        state = data.get("state")
        city = data.get("city")
        pincode = data.get("pincode")

        full_address = f"{address_line1}, {country},{state} ,{city} - {pincode}".strip(", ")

      

        id = request.session.get("product")
        try:
            # Verify payment signature
            params = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            client.utility.verify_payment_signature(params)

            # Save payment data
            product = Project.objects.get(id=id)
            seller_account = product.Project_id  
            seller_email = seller_account.email
            sale = sales(SaleId=product, PaymentId=razorpay_payment_id, BuyerAddress = full_address, BuyerMail = email)
            sale.save()

            update_project_revenue(product.id)
            subject = "Snippat Purchase Confirmation"
            name = product.Title
            msg = f"""
            Dear Customer,

            Thank you for your purchase on Snippat! We are pleased to inform you that your transaction was successful. Below are the details of your purchase:

            Product Name: {name}
            Purchase ID: {sale.id}
            Purchase Date: {sale.SaleDate.strftime('%Y-%m-%d %H:%M:%S')}
            Download Link: {product.project_file.url}

            If you have any questions or need further assistance, please feel free to contact our support team.

            Best regards,
            The Snippat Team
            """
            recipient_list = [email]  # List of recipient email addresses
            send_mail(subject, msg, 'snippat.service@gmail.com', recipient_list, fail_silently=False)

            return JsonResponse({'success': True, 'message': 'Payment successful. If the download button didn\'t appear, check your email for the download link.'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def update_project_revenue(project_id):
    """ Manually update total revenue for a given project """
    try:
        project = Project.objects.get(id=project_id)
        total_sales = sales.objects.filter(SaleId=project).count()
        total_revenue = total_sales * project.price 
        revenue, created = ProjectRevenue.objects.get_or_create(project=project)
        revenue.total_revenue = total_revenue
        revenue.save()

        return f"Revenue updated: {revenue.total_revenue}"
    except Project.DoesNotExist:
        return "Project not found"
"""def transfer_funds(amount, account_id):
    try:
        bank_details = BankDetails.objects.get(bankid=account_id)
        transfer_response = client.transfer.create({
            "amount": int(amount * 100),
            "currency": "INR",
            "account": bank_details.LinkId
        })
        
        # Save transfer details
        Payouts.objects.create(
            PayoutBankID=bank_details,
            PaidAmount=amount,
            TransferId=transfer_response["id"],
            ProductId=sales.objects.latest('id')
        )
        
        print("Transfer Successful:")
        print(json.dumps(transfer_response, indent=4))  # Pretty print response
        
        return {"success": True, "response": transfer_response}
    
    except BankDetails.DoesNotExist:
        error_message = "Error: Bank details not found for account ID {}".format(account_id)
        print(error_message)
        return {"success": False, "error": error_message}
    
    except Exception as e:
        error_message = "Unexpected error occurred: {}".format(str(e))
        print(error_message)
        return {"success": False, "error": error_message}"""

def get_payout_data(request):
    try:
        # Extract token and get user ID
        access_token = request.headers.get("Authorization", "").split(" ")[-1]
        decoded_token = UntypedToken(access_token)
        user_id = decoded_token["user_id"]

        # Get user
        user = account.objects.get(id=user_id)

        # Get filter type and calculate start date
        filter_type = request.GET.get("filter", "7days")
        num_days = {"7days": 7, "30days": 30, "lastyear": 365}.get(filter_type, 7)
        start_date = timezone.now() - timedelta(days=num_days)

        # Fetch withdrawal requests for the user with status "done"
        withdrawals = (
            WithdrawRequest.objects.filter(WithdrawID=user, Date__gte=start_date, Status="done")
            .values("Date", "Amount")
            .order_by("Date")
        )

        if not withdrawals:
            return JsonResponse({"message": "No withdrawals found"}, safe=False)

        # Format data for Chart.js
        formatted_data = [
            {"date": withdraw["Date"].strftime("%Y-%m-%d"), "amount": withdraw["Amount"] or 0}
            for withdraw in withdrawals
        ]

        return JsonResponse(formatted_data, safe=False)

    except account.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)



def market_sale(request):
    query = request.GET.get('q', '')
    projects = Project.objects.filter(Title__icontains=query) if query else Project.objects.all()
    
    if query and not projects.exists():
        messages.error(request, "No projects found.")

    return render(request, 'market.html', {'project': projects, 'query': query})