from django.db import models
import uuid
from django.utils import timezone
from datetime import timedelta




# Create your models here.
class account(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=100,unique=True,null=True)

    role = models.CharField(max_length=100,null=True)

    email = models.EmailField(unique=True,null=True)
    password = models.CharField(max_length=200,null=True)

    Subscription = models.BooleanField(default=False)
    SubPlan = models.CharField(max_length=100,null=True)

    startDate = models.DateTimeField(null=True, blank=True)
    endDate = models.DateTimeField(null=True, blank=True)

    payment_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add= True,null = True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4()
        super().save(*args, **kwargs)

class Project(models.Model):
    Project_id = models.ForeignKey(account,on_delete=models.CASCADE)
    Title = models.CharField(max_length=255)
    ProjectDis = models.TextField()
    includes = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default='USD')
    PriviewLink = models.URLField(null=True, blank=True)
    drive_link = models.URLField(null=True, blank=True)
    PreviewImage = models.ImageField(upload_to='preview_images/', null=True, blank=True)
    project_file = models.FileField(upload_to='project_files/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add= True,null = True)
class ProjectFile(models.Model):
    project = models.ForeignKey(Project, related_name='files', on_delete=models.CASCADE)
    file = models.FileField(upload_to='projects/',null=True)



class KYCCapturedPhoto(models.Model):
    kyc_id = models.ForeignKey(account, on_delete=models.CASCADE)
    photo1 = models.ImageField(upload_to='kyc/photos/',null=True)  # Left face photo
    photo2 = models.ImageField(upload_to='kyc/photos/',null=True)  # Center face photo
    photo3 = models.ImageField(upload_to='kyc/photos/',null=True)  # Right face photo
    front = models.ImageField(upload_to='kyc/documents/',null=True)  # Front document photo
    back = models.ImageField(upload_to='kyc/documents/',null=True)  # Back document photo
    verified = models.BooleanField(default=False, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class BankDetails(models.Model):
    bankid = models.ForeignKey(account,on_delete=models.CASCADE)
    LinkId = models.CharField(max_length=100,null=True)
    AccountName = models.CharField(max_length=100,null=True)
    AccountNo = models.IntegerField(null=True)
    IFSC = models.CharField(max_length=100,null=True)
    BankName = models.CharField(max_length=100,null=True)

class sales(models.Model):
    SaleId = models.ForeignKey(Project,on_delete= models.CASCADE)
    PaymentId = models.CharField(max_length=100,null = True)
    SaleDate = models.DateTimeField(auto_now_add=True,null=True)
    