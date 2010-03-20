from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.utils import simplejson
from django.template import RequestContext

import re

from models import *
from forms import *
from querybuilder.models import *
from querybuilder.decorators import superuser_only
from encoders import json_table_encoder, json_graph_encoder

def get_context(request):
    return RequestContext(request)
### View-mode view functions ###

@login_required
def index(request):
    dashboards = Dashboard.objects.filter(active = True)
    return render_to_response('dashboard/main.html', {'dashboards': dashboards, 'mode': 'view'}, context_instance = get_context(request))

@login_required
def dashboard(request, dashboard_id):
    dashboard = get_object_or_404(Dashboard, id = dashboard_id)
    if dashboard.active == False:
        raise Http404()
    return render_to_response('dashboard/dashboard.html', {'dashboard': dashboard, 'mode': 'view'}, context_instance = get_context(request))

@login_required
def view_element(request, dashboard_id, element_id, column_id = None):
    dashboard = get_object_or_404(Dashboard, id = dashboard_id)
    element = get_object_or_404(Element, id = element_id)
    raw_data_list = []
    for data_selection in element.get_data_selections():
        raw_data_list += [data_selection.get_data(None)]
    
    return render_to_response('dashboard/view_element.html', {'data': raw_data_list, 'dashboard_id': dashboard_id, 'element_id': element_id, 'dashboard': dashboard, 'element': element, 'mode': 'element'}, context_instance = get_context(request))

@login_required
def data(request, dashboard_id = None, element_id = None, column_id = None):
    data = get_data(dashboard_id, element_id, column_id);
        
    return HttpResponse(data, mimetype='text/json')

### View helper functions ###

def get_data(dashboard_id, element_id, column_id, encode = True, explain = False):
    element = get_object_or_404(Element, id = element_id)

    main_data = []
    # Retrieve required data
    if column_id == None:
        data_selections = element.get_data_selections()
        data_list = []
        for data_selection in data_selections:
            data_list += [data_selection.get_data(None, explain = explain)]
        if explain != True:
            formatted_data_list = element.get_child().format_data(data_list)
            main_data = formatted_data_list
        else:
            main_data = data_list
    else:
        column = get_object_or_404(DataColumn, id = column_id)
        main_data = column.get_data()

    if not encode:
        return main_data

    # Encode it in the appropriate format
    if element.get_type() == "graph":
        data = json_graph_encoder.encode(main_data)
    elif element.get_type() == "table":
        data = json_table_encoder.encode(main_data)
    else:
        data = simplejson.JSONEncoder.encode(main_data)

    return data

### Redirections ###

def redirect_to_design():
    return HttpResponseRedirect('/dashboard/design/')

def redirect_to_edit_element(element):
    return HttpResponseRedirect('/dashboard/design/edit_element/%d/' % element.id)

### Design-mode views ###

@superuser_only
def design(request):
    dashboards = Dashboard.objects.all()
    return render_to_response('dashboard/design/design.html', {'dashboards': dashboards, 'mode': 'design', 'design': True}, context_instance = get_context(request))

@superuser_only
def add_dashboard(request):
    form = DashboardForm()

    if request.method == 'POST':
        form = DashboardForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect_to_design()

    return render_to_response('dashboard/design/add_dashboard.html', {'form': form}, context_instance = get_context(request))

@superuser_only
def init_dashboard(request, dashboard_id):
    """
    This view will put your dashboard on the fast-track by pre-populating your dashboard using the application and models
    selected.

    This method is long and messy. Sorry!
    """
    dashboard = get_object_or_404(Dashboard, id = dashboard_id)    
    from querybuilder.models import get_apps, get_models_in_app
    app = None
    models = None
    selected_models = []
    avg_rows = None
    
    if request.method == 'POST':
        if 'app' in request.POST and request.POST['app'] in get_apps():
            app = request.POST['app']
            add_models_from_app(app)
        if 'model' in request.POST:
            selected_models = request.POST.getlist('model') # TODO: Verify each of selected_models in get_models_in_app(app)!
    if app:
        models_in_app = get_models_in_app(app)
        avg_rows = 0
        models = []
        for model_obj, model_name in models_in_app:
            count = model_obj.objects.all().count()
            avg_rows += count
        avg_rows = avg_rows / len(models_in_app)
        for model_obj, model_name in models_in_app:
            count = model_obj.objects.all().count()
            more_than_avg = False
            if avg_rows < count:
                more_than_avg = True
            models += [{'obj': model_obj, 'name': model_name, 'count': count, 'mta': more_than_avg}]

    if selected_models:
        
        # First simply generate a bar graph and a table with the amount of objects in each model
        
        ds_list = []
        for model in selected_models:
            ds = DataSelection(name = 'All objects in %s' % model)
            ds.save() # This seeds the DataModels
            ds.selected_model = DataModel.objects.get(model_name = model, app_name = app) # TODO: catch exception in case seeding didn't work
            ds.save() # We should have a working DataSelection now
            ds_list += [ds]
            
        elm = Graph(dashboard = dashboard, name = 'Total number of objects', graph_type = 'bar')
        elm.count_series = True
        elm.save()
        for ds in ds_list:
            elm.data.add(ds) # That's all for simply counting the numbers of objects
        elm.save()

        elm = Table(dashboard = dashboard, name = 'Total number of objects')
        elm.count_series = True
        elm.save()
        for ds in ds_list:
            elm.data.add(ds) # That's all for simply counting the numbers of objects
        elm.save()

        # Now add a graph for each model with at least a date or datetime field

        for model in selected_models:
            model_obj = get_model(app, model) # get_model() from querybuilder/models.py
            fields = get_field_names_types_in_model(model_obj)
            datetime_field = None
            fk_field = None
            integer_field = None
            decimal_field = None
            id_field = None
            for (field_name, field_type, field_fk) in fields:
                if field_type == 'DateTimeField' and not datetime_field:
                    datetime_field = field_name
                if field_type == 'IntegerField' and not integer_field:
                    integer_field = field_name
                if field_type == 'DecimalField' and not decimal_field:
                    decimal_field = field_name
                if field_type == 'ForeignKey' and not fk_field:
                    fk_field = field_name
                if field_type == 'AutoField' and not id_field:
                    id_field = field_name

            DAY_LENGTH = 86400
            graph_types = ( ('MONTH', 0, 'per month', 'bar', 'right'), ('WEEK', DAY_LENGTH * 31, 'per week over last month', 'line', 'left'), ('DAY', DAY_LENGTH * 7, 'per day over last week', 'linepoint', 'right'), ('HOUR', DAY_LENGTH / 8, 'per hour over last 3 hours', 'bar', 'right'))
            
            ### Process model with datetime and FK ###
                    
            if datetime_field and fk_field:
                for graph_type_group_by, graph_type_max_seconds, graph_type_name, graph_type, graph_position in graph_types:
                    ds = DataSelection(name = '%s objects over time %s' % (model, graph_type_name))
                    ds.save()
                    ds.selected_model = DataModel.objects.get(model_name = model, app_name = app)
                    ds.auto_add_columns = True # Automatically add all DataColumns for this model
                    ds.save()
                    graph = Graph(dashboard = dashboard, name = '%ss over time %s' % (model, graph_type_name), graph_type = graph_type, position = graph_position)
                    graph.save()
                    graph.data.add(ds)
                    graph.x_axis = DataColumn.objects.get(selection = ds, name = datetime_field)
                    dt_column = graph.x_axis.get_child()
                    dt_column.group_by = graph_type_group_by
                    dt_column.order_by = 'asc'
                    dt_column.max_value = graph_type_max_seconds
                    dt_column.save()
                    graph.series = DataColumn.objects.get(selection = ds, name = fk_field)
                    fk_column = graph.series.get_child()
                    fk_column.group_by = True
                    fk_column.save()
                    id_column = DataColumnInteger(selection = ds, name = id_field, aggregate = 'Count')
                    id_column.save()
                    graph.y_axis = id_column
                    graph.save()

            ### Process model with datetime, fk and decimal/integer ###
            # TODO: Should work similar to above, plot the values of decimal/integer instead of counting

            if datetime_field and fk_field and integer_field:
                for graph_type_group_by, graph_type_max_seconds, graph_type_name, graph_type, graph_position in graph_types:
                    ds = DataSelection(name = '%s values over time %s' % (model, graph_type_name))
                    ds.save()
                    ds.selected_model = DataModel.objects.get(model_name = model, app_name = app)
                    ds.auto_add_columns = True # Automatically add all DataColumns for this model
                    ds.save()
                    graph = Graph(dashboard = dashboard, name = '%s values over time %s' % (model, graph_type_name), graph_type = graph_type, position = graph_position)
                    graph.save()
                    graph.data.add(ds)
                    graph.x_axis = DataColumn.objects.get(selection = ds, name = datetime_field)
                    dt_column = graph.x_axis.get_child()
                    dt_column.group_by = graph_type_group_by
                    dt_column.order_by = 'asc'
                    dt_column.max_value = graph_type_max_seconds
                    dt_column.save()
                    graph.series = DataColumn.objects.get(selection = ds, name = fk_field)
                    fk_column = graph.series.get_child()
                    fk_column.group_by = True
                    fk_column.save()
                    id_column = DataColumnInteger(selection = ds, name = integer_field)
                    id_column.save()
                    graph.y_axis = id_column
                    graph.save()

            if datetime_field and fk_field and decimal_field:
                for graph_type_group_by, graph_type_max_seconds, graph_type_name, graph_type, graph_position in graph_types:
                    ds = DataSelection(name = '%s values over time %s' % (model, graph_type_name))
                    ds.save()
                    ds.selected_model = DataModel.objects.get(model_name = model, app_name = app)
                    ds.auto_add_columns = True # Automatically add all DataColumns for this model
                    ds.save()
                    graph = Graph(dashboard = dashboard, name = '%s values over time %s' % (model, graph_type_name), graph_type = graph_type, position = graph_position)
                    graph.save()
                    graph.data.add(ds)
                    graph.x_axis = DataColumn.objects.get(selection = ds, name = datetime_field)
                    dt_column = graph.x_axis.get_child()
                    dt_column.group_by = graph_type_group_by
                    dt_column.order_by = 'asc'
                    dt_column.max_value = graph_type_max_seconds
                    dt_column.save()
                    graph.series = DataColumn.objects.get(selection = ds, name = fk_field)
                    fk_column = graph.series.get_child()
                    fk_column.group_by = True
                    fk_column.save()
                    id_column = DataColumnDecimal(selection = ds, name = decimal_field)
                    id_column.save()
                    graph.y_axis = id_column
                    graph.save()

            ### Process model with datetime and boolean ###
            # TODO: Should work similar to above, boolean is series
            
        return redirect_to_design()

    return render_to_response('dashboard/design/init_dashboard.html', {'dashboard': dashboard, 'apps': get_apps(), 'app': app, 'models': models,}, context_instance = get_context(request))

 ## AJAX POSTs ##

@superuser_only
def apply_layout(request, dashboard_id):
    dashboard = get_object_or_404(Dashboard, id = dashboard_id)
    columns = ['left', 'middle', 'right']
    for column in columns:
        if not column in request.POST:
            return HttpResponse("False")
    for column in columns:
        ret = dashboard.set_elements(re.findall('(\d+)', request.POST[column]), column)
        if not ret:
            return HttpResponse("False")
    return HttpResponse("True")

 ## Hide/show/delete stuff, might make these into a generic ##

@superuser_only
def hide_dashboard(request, dashboard_id):
    dashboard = get_object_or_404(Dashboard, id = dashboard_id)
    dashboard.active = False
    dashboard.save()
    return redirect_to_design()

@superuser_only
def show_dashboard(request, dashboard_id):
    dashboard = get_object_or_404(Dashboard, id = dashboard_id)
    dashboard.active = True
    dashboard.save()
    return redirect_to_design()

@superuser_only
def hide_element(request, element_id):
    elm = get_object_or_404(Element, id = element_id)
    elm.active = False
    elm.save()
    return redirect_to_design()

@superuser_only
def show_element(request, element_id):
    elm = get_object_or_404(Element, id = element_id)
    elm.active = True
    elm.save()
    return redirect_to_design()

@superuser_only
def delete_element(request, element_id):
    elm = get_object_or_404(Element, id = element_id)
    elm.delete()
    return redirect_to_design()

 ## Edit Dashboard elements ##

@superuser_only
def edit_element(request, element_id):
    element = get_object_or_404(Element, id = element_id)
    if element.get_type() == 'graph':
        if request.method == 'POST':
            form = GraphForm(request.POST, instance = element.get_child())
            if form.is_valid():
                ret = form.save()
        else:
            form = GraphForm(instance = element.get_child())
    elif element.get_type() == 'table':
        if request.method == 'POST':
            form = TableForm(request.POST, instance = element.get_child())
            if form.is_valid():
                form.save()
        else:
            form = TableForm(instance = element.get_child())
    request.session['return_url'] = '/dashboard/design/edit_element/%s/' % (element.id)
    return render_to_response('dashboard/design/edit_element.html', {'form': form, 'element': element, 'mode': 'design'}, context_instance = get_context(request))

@superuser_only
def add_element(request, dashboard_id):
    dashboard = get_object_or_404(Dashboard, id = dashboard_id)
    element_types = get_element_types()
    element_type = None

    if request.method == 'POST':
        if 'element_type' in request.POST:
            element_type = request.POST['element_type']
            
    if element_type and element_type in element_types.keys():
        element = element_types[element_type]()
        form = get_element_form(element)
    else:
        form = None
        element = None
        element_type = None

    if element and request.method == 'POST':
        if 'name' in request.POST:
            form = get_element_form(element, request.POST)
            if form.is_valid():
                ret = form.save()
                ret.position = 'left'
                ret.save()
                return redirect_to_design()
    request.session['return_url'] = '/dashboard/design/add_element/%s/' % (dashboard.id)
    return render_to_response('dashboard/design/add_element.html', {'form': form, 'element_types': element_types, 'element': element, 'element_type': element_type, 'design': True}, context_instance = get_context(request))

@superuser_only
def add_edit_tablecolumn(request, element_id, table_column_id = None):
    element = get_object_or_404(Element, id = element_id)
    table = element.get_child()

    if table_column_id:
        edit_tablecolumn = get_object_or_404(TableColumn, id = table_column_id)
        form = TableColumnForm(instance = edit_tablecolumn)
    else:
        edit_tablecolumn = None
        form = TableColumnForm()
        
    if request.method == 'POST':
        if edit_tablecolumn:
            form = TableColumnForm(request.POST, instance = edit_tablecolumn)
        else:
            form = TableColumnForm(request.POST)
            
        if form.is_valid():
            tablecolumn = form.save()
            if not edit_tablecolumn:
                table.column_elements.add(tablecolumn)
                table.save()
            return redirect_to_edit_element(element)

    return render_to_response('dashboard/design/add_tablecolumn.html', {'form': form, 'edit_tablecolumn': edit_tablecolumn}, context_instance = get_context(request))

@superuser_only
def delete_tablecolumn(request, tablecolumn_id):
    tc = get_object_or_404(TableColumn, id = tablecolumn_id)

    table = tc.column_elements_table_set.all()
    if table.count() > 0:
        table = table[0]
        tc.delete()
        return redirect_to_edit_element(table)
    tc.delete()
    return redirect_to_design()
