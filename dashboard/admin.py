from django.contrib import admin
from dashboard.models import *
import datetime

admin.site.register(Dashboard)

admin.site.register(Element)
admin.site.register(Graph)
admin.site.register(Table)
admin.site.register(TableColumn)
