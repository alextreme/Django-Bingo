from django.contrib import admin
from querybuilder.models import *
import datetime

admin.site.register(DataSelection)
admin.site.register(DataModel)

admin.site.register(DataColumn)
admin.site.register(DataColumnInteger)
admin.site.register(DataColumnBoolean)
admin.site.register(DataColumnDecimal)
admin.site.register(DataColumnDateTime)
admin.site.register(DataColumnString)
admin.site.register(DataColumnFK)

admin.site.register(ThresholdInteger)
admin.site.register(ThresholdDecimal)
