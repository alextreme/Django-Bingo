from django.conf.urls.defaults import *
from django.conf import settings

from views import *

urlpatterns = patterns('dashboard.views',
                       url(r'^$', 'index'),
                       
                       url(r'^design/$', 'design'),
                       url(r'^design/add_dashboard/', 'add_dashboard'),
                       url(r'^design/init_dashboard/(?P<dashboard_id>\d+)/$', 'init_dashboard'),                       
                       url(r'^design/add_element/(?P<dashboard_id>\d+)/$', 'add_element'),
                       url(r'^design/edit_element/(?P<element_id>\d+)/$', 'edit_element'),
                       url(r'^design/add_tablecolumn/(?P<element_id>\d+)/$', 'add_edit_tablecolumn', name='add_tablecolumn'),
                       url(r'^design/edit_tablecolumn/(?P<element_id>\d+)/(?P<table_column_id>\d+)/$', 'add_edit_tablecolumn', name='edit_tablecolumn'),                       
                       url(r'^design/delete_tablecolumn/(?P<tablecolumn_id>\d+)/$', 'delete_tablecolumn', name='delete_tablecolumn'),

                       url(r'^design/hide_dashboard/(?P<dashboard_id>\d+)/$', 'hide_dashboard'),
                       url(r'^design/show_dashboard/(?P<dashboard_id>\d+)/$', 'show_dashboard'),
                       url(r'^design/hide_element/(?P<element_id>\d+)/$', 'hide_element'),
                       url(r'^design/show_element/(?P<element_id>\d+)/$', 'show_element'),
                       url(r'^design/delete_element/(?P<element_id>\d+)/$', 'delete_element'),                       
                       url(r'^design/apply_layout/(?P<dashboard_id>\d+)/$', 'apply_layout'),
                       
                       url(r'^dash/(?P<dashboard_id>\d+)/', 'dashboard'),
                       url(r'^view_element/(?P<dashboard_id>\d+)/(?P<element_id>\d+)/', 'view_element'),
                       url(r'^data/(?P<element_id>\d+).json', 'data', name='json_data'),
                       url(r'^data/(?P<dashboard_id>\d+)/(?P<element_id>\d+).json', 'data'),
                       url(r'^data/(?P<dashboard_id>\d+)/(?P<element_id>\d+)/(?P<column_id>\d+).json', 'data'),                       
                       )

