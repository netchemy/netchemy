from django.contrib import admin

from .models import account,KYCCapturedPhoto,BankDetails,Project,ProjectFile
# Register your models here.

admin.site.register(account)
admin.site.register(KYCCapturedPhoto)
admin.site.register(BankDetails)
admin.site.register(Project)
admin.site.register(ProjectFile)