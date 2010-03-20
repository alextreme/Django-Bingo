from django.conf.urls.defaults import *
from django.conf import settings

from views import *

urlpatterns = patterns('querybuilder.views',
                       url(r'^$', 'index'),
                       url(r'^export_selection/(?P<selection_id>\d+)/$', 'export_selection', name='export_selection'),
                       url(r'^add_selection/$', AddSelectionWizard([AddSelectionStep1Form, AddSelectionStep2Form]), name='add_selection'),
                       url(r'^add_column/(?P<selection_id>\d+)/$', 'add_column', name='add_column'),
                       url(r'^edit_selection/(?P<selection_id>\d+)/$', 'edit_selection', name='edit_selection'),
                       url(r'^edit_column/(?P<selection_id>\d+)/(?P<column_id>\d+)/$', 'edit_column', name='edit_column'),
                       )

