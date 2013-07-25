from django.conf.urls.defaults import *
from django.views.generic import RedirectView

from django.conf import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^querybuilder/', include('querybuilder.urls')),                       
    (r'^dashboard/', include('dashboard.urls')),

    (r'^admin/', include(admin.site.urls)),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login'),
    (r'^accounts/profile/$', RedirectView.as_view(url='/')),
                       
    # These serve as a backup in case we don't have Apache serving static media
    # Not to be relied on in a production environment!
    (r'^media/(?P<path>.*)$','django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    (r'^admin_media/(?P<path>.*)$','django.views.static.serve', {'document_root': settings.ADMIN_MEDIA_ROOT}),
    (r'^$',  RedirectView.as_view(url='/dashboard/')),
 )
