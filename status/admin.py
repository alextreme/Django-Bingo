from django.contrib import admin
from models import *
import datetime

admin.site.register(HostStats)
admin.site.register(FilesystemStats)
admin.site.register(NetworkStats)
