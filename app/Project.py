from django.shortcuts import render,redirect
from django.contrib import messages
import re
import razorpay
from django.views.decorators.csrf import csrf_exempt
from .models import account,Project,KYCCapturedPhoto,BankDetails,ProjectFile,sales
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
import time

future_timestamp = int(time.time()) + (24 * 60 * 60) 
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
                return redirect('index')
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
        # Log the exception and return an error response
        print(f"Error: {e}")
        return JsonResponse({"error": "An error occurred while processing your request."}, status=500)

@csrf_exempt
def market_pay(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')

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
            sale = sales(SaleId=product, PaymentId=razorpay_payment_id)
            sale.save()

          

            
            transfer_response =  client.transfer.create({
                                "amount":1000,
                                "currency":"INR",
                                "account": "acc_Pf4xvSsq86LBIs"
                                })

            return JsonResponse({'success': True, 'message': 'Payment and transfer successful', 'transfer_response': transfer_response})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})