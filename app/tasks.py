import boto3
from celery import shared_task
from .models import KYCCapturedPhoto
from django.conf import settings
from netchemy.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
from django.core.mail import send_mail

@shared_task
def verify_faces(photo2_path, front_path, kycid):
    try:
        print(f"Processing images: {kycid}")

        # Initialize AWS Rekognition
        rekognition = boto3.client(
            "rekognition",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )

        # Read images as binary
        with open(front_path, 'rb') as f:
            front_image = f.read()
        with open(photo2_path, 'rb') as f:
            photo2_image = f.read()

        # Compare faces
        response = rekognition.compare_faces(
            SourceImage={'Bytes': front_image},
            TargetImage={'Bytes': photo2_image},
            SimilarityThreshold=50
        )

        print(response)
        # Check if faces match
        kyc_record = KYCCapturedPhoto.objects.get(id=kycid)
        if response.get('FaceMatches'):
            kyc_record.verified = True
            kyc_record.save()
            print("Face verification successful!")

            # Send success email
            send_mail(
                'Face Verification Successful',
                'Your face verification was successful.',
                settings.DEFAULT_FROM_EMAIL,
                [kyc_record.kyc_id.email],
                fail_silently=False,
            )
            return True
        else:
            kyc_record.delete()
            print("Face verification failed. KYC record deleted.")

            # Send failure email
            send_mail(
                'Face Verification Failed',
                'Your face verification failed and your KYC record has been deleted.',
                settings.DEFAULT_FROM_EMAIL,
                [kyc_record.kyc_id.email],
                fail_silently=False,
            )
            return False

    except Exception as e:
        print(f"Error in verify_faces task: {e}")
        return False
