from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(User)
admin.site.register(EmailVerification)
admin.site.register(VerificationLog)
admin.site.register(PhoneVerification)