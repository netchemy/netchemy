import base64
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import KYCCapturedPhoto,account
from rest_framework_simplejwt.tokens import UntypedToken
import json
from rest_framework.exceptions import AuthenticationFailed
from .tasks import verify_faces
from rest_framework.permissions import IsAuthenticated



class SubmitKYCView(View):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            # Extract and verify the token
            auth_header = request.headers.get('Authorization', None)
            if not auth_header or not auth_header.startswith('Bearer '):
                raise AuthenticationFailed("Token not provided or invalid format")

            access_token = auth_header.split(' ')[1]
            decoded_token = UntypedToken(access_token)
            user_id = decoded_token['user_id']
            user = account.objects.get(id=user_id)
            
            # frontend data
            data = json.loads(request.body)

            # Decode Base64 images
            photo1_data = base64.b64decode(data.get('photo1', '').split(',')[1] if data.get('photo1') else '')
            photo2_data = base64.b64decode(data.get('photo2', '').split(',')[1] if data.get('photo2') else '')
            photo3_data = base64.b64decode(data.get('photo3', '').split(',')[1] if data.get('photo3') else '')
            front_data = base64.b64decode(data.get('front', '').split(',')[1] if data.get('front') else '')
            back_data = base64.b64decode(data.get('back', '').split(',')[1] if data.get('back') else '')

            # Save images to model
            kyc_submission = KYCCapturedPhoto.objects.create(kyc_id=user)
            kyc_submission.photo1.save('photo1.jpg', ContentFile(photo1_data), save=False)
            kyc_submission.photo2.save('photo2.jpg', ContentFile(photo2_data), save=False)
            kyc_submission.photo3.save('photo3.jpg', ContentFile(photo3_data), save=False)
            kyc_submission.front.save('front.jpg', ContentFile(front_data), save=False)
            kyc_submission.back.save('back.jpg', ContentFile(back_data), save=False)
            kyc_submission.save()

            verify_faces.delay(kyc_submission.photo2.path, kyc_submission.front.path, kyc_submission.id)

            

            return JsonResponse({"message": "KYC submission successful!"}, status=201)
        except KeyError as e:
            return JsonResponse({"error": f"Missing key: {str(e)}"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)