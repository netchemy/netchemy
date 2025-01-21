from celery import shared_task
import face_recognition
from io import BytesIO
from PIL import Image, ImageEnhance
from .models import KYCCapturedPhoto
import numpy as np

@shared_task
def verify_faces(photo2_data, front_data, kyc_id):
    try:
        # Open images from byte data
        photo2_image = Image.open(BytesIO(photo2_data))
        front_image = Image.open(BytesIO(front_data))

        # Enhance the images to improve quality
        photo2_image = enhance_image(photo2_image)
        front_image = enhance_image(front_image)

        # Convert images to RGB
        photo2_rgb = photo2_image.convert("RGB")
        front_rgb = front_image.convert("RGB")

        # Get face encodings for both images
        photo2_face = face_recognition.face_encodings(np.array(photo2_rgb))
        front_face = face_recognition.face_encodings(np.array(front_rgb))

        # Check if both images have faces
        if len(photo2_face) > 0 and len(front_face) > 0:
            # Compare faces with a more strict tolerance (lower is stricter)
            matches = face_recognition.compare_faces(photo2_face, front_face, tolerance=0.5)

            if matches[0]:
                # If faces match, update the record as verified
                KYCCapturedPhoto.objects.filter(kyc_id=kyc_id).update(verified=True)
                return True  # Faces match
            else:
                # If faces don't match, delete the record
                KYCCapturedPhoto.objects.filter(kyc_id=kyc_id).delete()
                return False  # Faces don't match
        return False  # No faces found in one or both images

    except Exception as e:
        # Log or handle the exception properly
        print(f"Error in verify_faces task: {e}")
        return False  # Failure

def enhance_image(image):
    """
    Enhance the image quality to make face recognition more accurate.
    This can include resizing, contrast adjustment, and sharpening.
    """
    # Resize image to a consistent size (optional, based on typical image sizes)
    image = image.resize((600, 800))  # Resize as needed for consistency

    # Increase the contrast to enhance facial features
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)  # Adjust contrast (1.5 is an example)

    # Sharpen the image slightly for clearer features
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2.0)  # Adjust sharpness (2.0 is an example)

    return image
