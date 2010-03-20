from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.template import RequestContext

import excel

from models import *
from forms import *
from decorators import superuser_only

EDIT_SELECTION_MAX_DATA_LENGTH = 50

def get_context(request):
    return RequestContext(request)

### Redirection functions ###

def redirect_to_index():
    return HttpResponseRedirect('/querybuilder/')

def redirect_to_edit_selection(selection):
    return HttpResponseRedirect('/querybuilder/edit_selection/%s/' % selection.id)

### Query Builder non-modifying views ###

@superuser_only
def index(request):
    selections = DataSelection.objects.all()
    return render_to_response('querybuilder/data_selection_list.html', {'selections': selections}, context_instance = get_context(request))


@login_required
def export_selection(request, selection_id):  # Allow all users to export the data selection
    selection = get_object_or_404(DataSelection, id = selection_id)    
    try:
        data = selection.get_data()
        data_error = False
    except Exception, e:
        data_error = " Invalid data: " + e.message
        return HttpResponse(data_error)
    try:
        xls = excel.queryset_to_xls(data, selection)
    except Exception, e:
        raise e
#        raise Exception("Unable to turn QuerySet into Excel file: xlwt isn't installed")
    return xls

### Query Builder Selection/Column modifying views ###

@superuser_only
def add_column(request, selection_id):
    selection = get_object_or_404(DataSelection, id = selection_id)    
    column_types = get_column_types()
    column_type = None
    
    if request.method == 'POST':
        if 'column_type' in request.POST:
            column_type = request.POST['column_type']

    if column_type and column_type in column_types.keys():
        column = column_types[column_type]()
        form = get_column_form(column)
    else:
        form = None
        column = None
        column_type = None
    if request.method == 'POST':
        if 'name' in request.POST:
            form = get_column_form(column, request.POST)
            if form.is_valid():
                form.save()
                return redirect_to_edit_selection(selection)
        
    return render_to_response('querybuilder/add_column.html', {'types': column_types, 'column': column, 'form': form, 'column_type': column_type}, context_instance = get_context(request))

@superuser_only
def edit_column(request, selection_id, column_id):
    col = get_object_or_404(DataColumn, id = column_id)
    selection = get_object_or_404(DataSelection, id = selection_id)    
    if col.get_child(): # If we have a Column type, use that as instance instead
        col = col.get_child() 
    
    if request.method == 'POST':
        form = get_column_form(col, request.POST)
        if form.is_valid():
            ret = form.save()
            return redirect_to_edit_selection(selection)
    else:
        form = get_column_form(col)

    return render_to_response('querybuilder/edit_column.html', {'form': form, 'column': col, 'selection': selection}, context_instance = get_context(request))

@superuser_only
def edit_selection(request, selection_id):
    selection = get_object_or_404(DataSelection, id = selection_id)
    if request.method == 'POST':
        form = DataSelectionForm(request.POST, instance = selection)
        if form.is_valid():
            ret = form.save()
    else:
        form = DataSelectionForm(instance = selection)
    try:
        explain = selection.get_data(explain = True)
    except Exception, e:
        explain = " Invalid SQL query: " + str(e)

    try:
        as_python = selection.get_data(as_python = True)
    except Exception, e:
        as_python = " Invalid Python: " + str(e)
    try:
        max_data_exceeded = False        
        data = selection.get_data()
        data_error = False
    except Exception, e:
#        raise e
        data = []
        data_error = u" Invalid data: " + str(e)

    return render_to_response('querybuilder/edit_selection.html', {'form': form, 'selection': selection, 'explain': explain, 'data': data, 'max_data_exceeded': max_data_exceeded, 'data_error': data_error, 'as_python': as_python, 'request': request}, context_instance = get_context(request))
