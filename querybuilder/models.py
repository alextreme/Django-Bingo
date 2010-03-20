from django.db import models
from django.conf import settings
from django.db.models import Avg, Min, Max, Sum, Count # Dashboard designer can use these for a data selection
from django.utils import simplejson

import sys
import datetime

global_max_length = 200
global_max_length_small = 40

def get_apps():
    return settings.INSTALLED_APPS

def get_apps_tuple():
    choices = []
    for app in get_apps():
        choices += [ (app, app) ]
    return choices

def get_model(app_name, model_name):
    """
    Given an application and model name, return the imported model as specified by
    model name.
    """
    assert app_name
    assert model_name
    
    try:
        curr_models = __import__(app_name + '.models', globals(), locals(), [model_name], -1)
    except:
        raise Exception("Unable to import application models from %s.models, model name: %s" % (app_name, model_name))
    try:
        return curr_models.__dict__[model_name]
    except Exception, e:
        raise e # FIXME: Unable to find the requested model

def get_models_in_app(app_name):
    """
    Return a list of 2-tuples containing all models in the given app.
    Each tuple contains the model and model name.
    """
    model_list = []
    app_models = __import__(app_name, globals(), locals(), ['models'], -1) # Could also do this with imp...
    app_models = app_models.models
    for key, elm in app_models.__dict__.iteritems():
        try:
            if issubclass(elm, models.Model): # Only need the models, thank you
                model_list += [(elm, elm._meta.object_name)]
        except Exception, e:
            pass # elm isn't a class?
    return model_list

def add_models_from_app(app_name):
    # For all models in the specified application
    models = get_models_in_app(app_name)
    for (model, model_name) in models:
        try: # Add a data-model entry (if it doesn't exist already)
            dm = DataModel(model_name = model_name, app_name = app_name)
            dm.save()
        except Exception, e:
            pass
            #raise e # Probably already have these loaded in?    

def get_fields_in_model(model):
    return model._meta.local_fields

def get_field_names_types_in_model(model):
    fields = get_fields_in_model(model)
    field_list = []
    for field in fields:
        if field.get_internal_type() == 'ForeignKey':
            field_list += [(field.name, field.get_internal_type(), field.related.parent_model)]
        else:
            field_list += [(field.name, field.get_internal_type(), None)]
    return field_list

def get_column_types():
    return {'integer': DataColumnInteger,
            'boolean': DataColumnBoolean,
            'decimal': DataColumnDecimal,
            'string': DataColumnString,
            'datetime': DataColumnDateTime,
            'foreign_key': DataColumnFK,
             }
             

### Data selection models ###

class DataSelection(models.Model):
    """
    DataSelection is the main model to access Query Builder.
    Simply set up a DataSelection and call 'get_data()' on it to retrieve
    a QuerySet with the specified data.
    """

    name = models.CharField("Name for this data selection", max_length = global_max_length) # Used to identify this data selection in the admin
    selected_model = models.ForeignKey('DataModel', related_name = 'selected_model_data_selection_set', blank = True, null = True) # PingResult
    auto_add_columns = models.BooleanField(default = 0)    
    limit_to = models.IntegerField(default = 0)
    count_series_label = models.CharField(max_length = global_max_length, blank = True, help_text = 'Override the count series label for this data selection. If not defined, the model name will be used instead.')
    manager_method = models.CharField(max_length = global_max_length, blank = True, help_text = 'By default we retrieve the objects via Foo.objects.all(). Specify the Manager method used, eg. enter "bar" to access the objects via Foo.objects.bar()')

    extra_select = models.TextField("Extra SELECT SQL statements", blank = True, help_text = 'A JSON dictionary, assign attribute names to SQL clauses. Use the attribute names as a DataColumn "name" for usage in a DataElement. Each name and SQL clause must be a string. Example: {"foo": "bar > \'20\'", "foobar": "SELECT COUNT(*) FROM blog_entry WHERE blog_entry.blog_id = blog_blog.id"}')
    extra_tables = models.TextField("Extra FROM SQL statement", blank = True, help_text = 'A JSON list of strings. If you are using tables not normally retrieved in the QuerySet via the extra select/where/order_by clauses, add the table name(s) here. Do not add the table names of tables already used. Example: ["my_blog_posts", "my_blog_comments"]')
    extra_where = models.TextField("Extra WHERE SQL statement", blank = True, help_text = 'A JSON list of strings. All strings are "AND"ed together to form the SQL Where statement. Example: ["my_blog_posts.blog_id > 200", "my_blog_comments.posted = NULL"]')
    extra_order_by = models.TextField("Extra ORDER BY SQL statement", blank = True, help_text = 'A JSON list of strings. Use this field to add any extra ordering for clauses defined above. Example: ["my_blog_posts.blog_id", "my_blog_comments.date"]')

    def __unicode__(self):
        return "%s (on %s)" % (self.name, self.selected_model)

    def has_extra_set(self):
        if self.extra_select != "" or self.extra_tables != "" or self.extra_where != "" or self.extra_order_by != "":
            return True
        return False

    def get_extra_select(self):
        """
        Return the given self.extra_select field as a Python dictionary. The data entered is presumed to be a JSON dictionary.
        Raise an Exception if self.extra_select is invalid, and an empty dictionary if the field is empty.
        """
        
        s = self.extra_select.strip()
        if s == "":
            return {}
        d = simplejson.loads(s)
        if not type(d) == type({}):
            raise Exception("DataSelection %s has an incorrect select clause, not a dictionary" % (self.name))
        for key, item in d.iteritems():
            if type(key) != type(u"") or type(item) != type(u""):
                raise Exception("DataSelection %s has an incorrect select clause, invalid key/item in dictionary (both must be strings)" % (self.name))
        return d

    def parse_json_list(self, s, field_name = ""):
        """
        Given string s is parsed as JSON data and returned as a list of strings.
        Returns an empty list if s is empty, raises an Exception if the JSON data is invalid.
        """
        
        s = s.strip()
        if s == "":
            return []
        l = simplejson.loads(s)
        if not type(l) == type([]):
            raise Exception("DataSelection %s has an incorrect %s clause, not a list" % (self.name, field_name))
        for item in l:
            if type(item) != type(u"") and type(item) != type(""):
                raise Exception("DataSelection %s has an incorrect %s clause, invalid item in list (all items must be strings)" % (self.name, field_name))
        return l

    def get_extra_where(self):
        return self.parse_json_list(self.extra_where, "where")

    def get_extra_tables(self):
        return self.parse_json_list(self.extra_tables, "tables")    
    
    def get_extra_order_by(self):
        return self.parse_json_list(self.extra_order_by, "order_by")

    def get_columns(self):
        """
        Retrieve all columns with a relation to this data selection.
        """
        return self.datacolumn_related.all().order_by('name')

    def get_aggregate_columns(self):
        return self.get_columns().exclude(aggregate = "")

    def get_ordering_columns(self):
        return self.get_columns().exclude(order_by = "")

    def get_group_by_columns(self):
        """
        Retrieve a tuple with 2 lists. The first list contains
        all columns which GROUP BY should be applied on. The second
        list contains the exact elements that should be used in a
        GROUP BY SQL statement.

        If no GROUP BY columns exist, return 2 empty lists.
        """
        
        columns = self.get_columns()
        g_by_columns = []
        g_by_elements = []
        for column in columns:
            if column.get_group_by():
                g_by_columns += [column]
                g_by_elements += [column.get_group_by()]
        return (g_by_columns, g_by_elements)

    def get_filter_columns(self):
        columns = self.get_columns()
        filter_columns = []
        filter_elements = []
        for column in columns:
            if column.get_filter():
                filter_columns += [column]
                filter_elements += [column.get_filter()]
        return (filter_columns, filter_elements)

    def get_data(self, element = None, limit = None, explain = False, as_python = False):
        """
        Retrieve the data as specified by this data-selection.
        Uses various forms of introspection into django models to retrieve the (meta)data.

        The data returned is a list of dict's, each dict is for a single group-by model object, with dict['data']
        containing the values retrieved from the 'selected-model' objects connected to this group-by object.

        The element for which this selection is used can be given: this way we can format the data
        in the required format (graphs -> x/y data, table -> [a..z]).
        If no element is given, dict['data'] contains the queryset containing the 'selected-model' objects.

        The limit given determines the number of elements per group-by object to select. FIXME: add ordering?
        """
        model = self.get_model()
        manager_method = "all"
        if self.manager_method != '' and self.manager_method in dir(model.objects):
            manager_method = self.manager_method
        data_qs = eval("model.objects.%s()" % manager_method)
        py_string_list = ["qs = %s.objects.%s()" % (model._meta.object_name, manager_method)]
    
        ### Data grouping
        (g_by_columns, g_by_elements) = self.get_group_by_columns()        
        if g_by_elements:
            data_qs.query.group_by = g_by_elements
            py_string_list.append("qs.query.group_by = %s" % ("['" + "','".join(g_by_elements) + "']"))

        ### Data filtering
        (filter_columns, filter_elements) = self.get_filter_columns()
        if filter_elements:
            data_qs = eval("data_qs.filter(%s)" % (",".join(filter_elements)))
            py_string_list[0] += ".filter(%s)" % (",".join(filter_elements))

        ### Data Date-grouping
        if g_by_columns:
            for column in g_by_columns:
                if column.get_type() == 'datetime':
                    d_dist = column.get_child().get_date_distinct()
                    (d_format_string, d_format_type) = column.get_child().get_date_distinct_format_string()

                    if d_dist != None and d_format_string != None:
                        # I'd rather have done this directly with dates(), but the main problem is
                        # that we lose all our other (non-datetime) fields. Might be a useful change to Django
                        # to be able to use dates() without cutting out all other fields.
                        
                        d = dict()
                        if d_format_type == 'datetime':
                            d[str(column.name)] = '(SELECT DISTINCT CAST(DATE_FORMAT(`' + column.name + '`, "' + d_format_string + '") AS DATETIME))' # Lifted from the Django dates() code
                        elif d_format_type == '': # don't wrap to datetime
                            d[str(column.name)] = 'DATE_FORMAT(`' + column.name + '`, "' + d_format_string + '")' # Lifted from the Django dates() code
                        # Hello, can you say 1337 h4x? No? Right, it's messy
                        # Note that 'column.name' MUST be put in here instead of using select_params, as params are given
                        # to mysqldb and quoted again, which leads to MySQL not being able to find the correct column.
                        data_qs = data_qs.extra(select = d)
                        py_string_list.append("qs = qs.extra(select = %s)" % ("{'%s': '%s' }" % (str(column.name), d[str(column.name)])))

                    if d_dist != None and d_format_string == None:
                        raise Exception("Unable to group by date for %s, unimplemented" % (d_dist))
                        
        ### Data extra's (if given)
        if self.has_extra_set():
            data_qs = data_qs.extra(select = self.get_extra_select(),
                                    tables = self.get_extra_tables(),
                                    where = self.get_extra_where(),
                                    order_by = self.get_extra_order_by())
            py_string_list.append("qs = qs.extra(select = %s, tables = %s, where = %s, order_by = %s)" % ("[" + ",".join(self.get_extra_select()) + "]", "[" + ",".join(self.get_extra_tables()) + "]", "[" + ",".join(self.get_extra_where()) + "]", "[" + ",".join(self.get_extra_order_by()) + "]"))
            
        ### Data aggregation / annotation (must be after filtering, else filter doesn't apply)
        for agg_column in self.get_aggregate_columns():
            data_qs = eval("data_qs.annotate(%s = %s)" % (agg_column.name, agg_column.get_aggregate()))
            py_string_list.append("from django.db.models import Avg, Min, Max, Sum, Count")
            py_string_list.append("qs = qs.annotate(%s = %s)" % (agg_column.name, agg_column.get_aggregate()))

        ### Data ordering (overrides ordinary model ordering)
        ordering = self.get_ordering_columns()
        if ordering:
            f = lambda x: x.get_ordering_name()
            ordering_arguments = map(f, ordering)
            data_qs = data_qs.order_by(*ordering_arguments)
            py_string_list.append("qs = qs.order_by(%s)" % ("[" + ",".join(ordering_arguments) + "]"))
        else:
            data_qs = data_qs.order_by()
            py_string_list.append("qs = qs.order_by()")

        ### Data limiting. Use limit to override self.limit_to
        field_names = []
        data_qs_limit = None
        if limit != None:
            data_qs_limit = limit
        elif self.limit_to != 0:
            data_qs_limit = self.limit_to
            
        if data_qs_limit:
            data_qs = data_qs[:data_qs_limit]
            py_string_list.append("qs = qs[:%d]" % (data_qs_limit))

        if explain:
            return unicode(data_qs.query)

        if as_python:
            return unicode("\n".join(py_string_list))

        data_qs.count_series_label = self.count_series_label

        ### Data formatting
        if element == None: # Return the 'pure' QuerySet for this selection
            return data_qs
        else: # Check all element types, return data as required by that type. 
            data_qs = element.get_child().format_data(data_qs)
        return data_qs

    def get_model(self):
        if self.selected_model:
            return get_model(self.selected_model.app_name, self.selected_model.model_name)
        return None

    def prepopulate_columns(self):
        """
        For this model determine which fields can be used to pre-populate the DateColumn subclasses for this data selection.
        """
        model = self.get_model()
        if model != None:
            # Pre-populate the DataColumn fields
            field_list = get_field_names_types_in_model(model)
            for (f_name, f_type, f_model) in field_list:
                if f_type == 'DateTimeField':
                    dc = DataColumnDateTime()
                elif f_type == 'DecimalField':
                    dc = DataColumnDecimal()
                elif f_type == 'CharField':
                    dc = DataColumnString()
                elif f_type == 'ForeignKey':
                    dc = DataColumnFK()
                    model_name = f_model._meta.object_name
                    model = DataModel.objects.get(model_name = model_name)
                    try:
                        pass
                    except: # Couldn't find the DataModel that this ForeignKey is associated to, ignoring this column
                        continue
                    dc.model = model # \o/
                elif f_type == 'IntegerField':
                    dc = DataColumnInteger()
                elif f_type == 'BooleanField':
                    dc = DataColumnBoolean()
                else:
                    continue # Unsupported type for now, sorry :)
                dc.name = f_name
                dc.selection = self
                dc.save()
                
    def save(self, *args, **kwargs):
        """
        When selecting a new model and when specified to auto-add columns, prepopulate the columns of this data selection.

        When we've selected an application we don't yet have any models for in our database, prepopulate the DataModel model
        with the models in the application.
        """

        new_obj = False
        try:
            old_instance = DataSelection.objects.get(pk = self.pk)
        except Exception, e:
            # Couldn't find the old instance, this must be a new assessment
            new_obj = True
                                                    
        super(DataSelection, self).save(*args, **kwargs)

        # Only attempt to add datacolumns when selected_model has been set for the first time and when the user has requested it
        if (not new_obj and self.selected_model != None and old_instance.selected_model == None) or (new_obj and self.selected_model != None):
            if self.auto_add_columns == True:
                self.prepopulate_columns()
        super(DataSelection, self).save(*args, **kwargs)

        if not new_obj: # Only attempt to add models when initializing our DataSelection
            return 

        super(DataSelection, self).save(*args, **kwargs)
                        
class DataModel(models.Model):
    app_name = models.CharField("Application / Data source", max_length = global_max_length, choices = get_apps_tuple())
    model_name = models.CharField(max_length = global_max_length, unique = True)

    def __unicode__(self):
        return "%s from app %s" % (self.model_name, self.app_name)

### Data Column Definitions ###

AGGREGATE_CHOICES = ( ('Avg', 'Average'), ('Min', 'Minimum'), ('Max', 'Maximum'), ('Count', 'Count'), ('Sum', 'Sum') )

ORDER_CHOICES = ( ('asc', 'Ascending'), ('desc', 'Descending') )
        
class DataColumn(models.Model):
    selection = models.ForeignKey(DataSelection, related_name = '%(class)s_related')
    name = models.CharField(max_length = global_max_length) # name of the element in the DataModel selection
    aggregate = models.CharField(max_length = global_max_length, choices = AGGREGATE_CHOICES, blank = True)
    order_by = models.CharField(max_length = global_max_length_small, choices = ORDER_CHOICES, blank = True)
    
    def __unicode__(self):
        extra_text = u""
        c_type = u""
        if self.get_child():
            try:
                extra_text = self.get_child().get_info()
                c_type = self.get_type()
            except:
                pass
        return "Column %s (%s, %s) %s" % (self.name, c_type, self.selection, extra_text)

    def get_thresholds(self):
        if self.get_child():
            return self.get_child().get_thresholds()
        return []

    def get_data(self):
        if self.get_child():
            try:
                return self.get_child().get_data()
            except:
                pass
        return None

    def get_name(self): # Not sure why I put this in here, no DataColumn subclasses have a name...
        if self.get_child():
            try:
                return self.get_child().get_name()
            except:
                pass
        return self.name

    def get_ordering_name(self):
        if self.order_by:
            if self.order_by == 'asc':
                return self.name
            return '-%s' % (self.name)
        return ''

    def get_filter(self):
        if self.get_child():
            try:
                return self.get_child().apply_filter()
            except:
                pass
        return None

    def get_aggregate(self):
        if self.aggregate:
            return "%s('%s')" % (self.aggregate, self.name)
        return None

    def get_group_by(self, force = False):
        """
        Determine if this column should be grouped, returns boolean.
        """
        child = self.get_child()
        if child:
            try:
                if child.get_group_by(force):
                    return child.get_group_by(force)
            except:
                pass
        return False

    def get_type(self):
        if self.get_child():
            return self.get_child().get_type()
        return None

    def get_child(self):
        """
        Get the subclass-object if there is one. Return None if there isn't.
        There has to be a neater way to do this...
        """
        try:
            if self.datacolumndatetime:
                return self.datacolumndatetime
        except:
            pass
        try:
            if self.datacolumndecimal:
                return self.datacolumndecimal
        except:
            pass
        try:
            if self.datacolumnstring:
                return self.datacolumnstring
        except:
            pass
        try:
            if self.datacolumninteger:
                return self.datacolumninteger
        except:
            pass
        try:
            if self.datacolumnboolean:
                return self.datacolumnboolean
        except:
            pass
        try:
            if self.datacolumnfk:
                return self.datacolumnfk
        except:
            pass
        return None

DATETIME_SQL_PERIOD_NAMES = [ ('DAY', 'Day'), ('WEEK', 'Week'), ('DAYOFWEEK', 'Day of the week'),('MONTH', 'Month'), ('YEAR', 'Year'), ('HOUR', 'Hour'), ('MINUTE', 'Minute'), ('QUARTER', 'Quarter') ]

class DataColumnDateTime(DataColumn):
    max_value = models.IntegerField(default = 0, blank = True, null = True, help_text = 'Max number of seconds ago. Use 0 to disable. 3600 = 1 hour, 86400 = 1 day, 604800 = 1 week, 2592000 = 1 month, 31536000 = 1 year')
    group_by = models.CharField(max_length = global_max_length, choices = DATETIME_SQL_PERIOD_NAMES, blank = True)
    group_by_limit = models.BooleanField(default = 0, help_text = 'When both max value and group by are chosen, enable this to increase max value dynamically to the nearest group by entity. Example: if you set max_value to 1, group_by to Hour and this field, max_value will increase to the beginning of the latest hour')

    def get_thresholds(self):
        return []

    def apply_filter(self):
        """
        Depending on the values set for this column, limit the data for the related data selection to values
        greater than or equal to the limit set (if any).
        Returns a Django-filter string that sets the limit, or None if there isn't one.
        """
        
        if self.max_value > 0:
            if self.group_by_limit == False or self.group_by == False:
                return "%s__gte = '%s'" % (self.name, datetime.datetime.now() - datetime.timedelta(0, self.max_value))
            else:
                max_val = datetime.datetime.now() - datetime.timedelta(0, self.max_value)
                max_val = max_val.replace(second = 0, microsecond = 0)
                if self.group_by == 'HOUR':
                    max_val = max_val.replace(minute = 0)
                if self.group_by == 'DAY':
                    max_val = max_val.replace(hour = 0, minute = 0)
                if self.group_by == 'DAYOFWEEK':
                    max_val = max_val.replace(hour = 0, minute = 0)                    
                if self.group_by == 'WEEK': # FIXME: need to calculate the earliest date of this week, grouping by day
                    max_val = max_val.replace(hour = 0, minute = 0)
                if self.group_by == 'MONTH':
                    max_val = max_val.replace(day = 1, hour = 0, minute = 0)
                if self.group_by == 'QUARTER': # FIXME: need to calculate the earliest date of this quarter, grouping by month
                    max_val = max_val.replace(day = 1, hour = 0, minute = 0)
                if self.group_by == 'YEAR':
                    max_val = max_val.replace(month = 1, day = 1, hour = 0, minute = 0)
                return "%s__gte = '%s'" % (self.name, max_val)
        return None

    def get_group_by(self, force = False):
        if self.group_by != "" or force:
            return "%s(%s)" % (self.group_by, self.name)
        return None

    def get_info(self):
        return "Limited to %d seconds ago" % (self.max_value)

    def get_date_distinct(self):
        if self.group_by:
            return self.group_by
        return None

    def get_date_distinct_format_string(self):
        """
        Return the SQL (probably only MySQL) date/datetime format for grouping this column by.
        This gives us the canonical date by which we group, instead of the separate dates.
        Example: 2009-12-01 instead of 2009-12-05 + 2009-12-21 + 2009-12-27 when grouping by month.
        """
        format_string = None
        f_type = 'datetime'
        if self.group_by == 'HOUR':
            format_string = "%%Y-%%m-%%d %%H:00:00"
        if self.group_by == 'MINUTE':
            format_string = "%%Y-%%m-%%d %%H:%%i:00"
        if self.group_by == 'DAY':
            format_string = "%%Y-%%m-%%d 00:00:00"
        if self.group_by == 'DAYOFWEEK':
            format_string = "%%w) %%W" # Hack to keep DOTW ordered...
            f_type = ''
        if self.group_by == 'WEEK': # FIXME: need to calculate the earliest date of the week?
            format_string = "%%Y-%%m-%%d 00:00:00"
        if self.group_by == 'MONTH':
            format_string = "%%Y-%%m-01 00:00:00"
        if self.group_by == 'QUARTER': # FIXME: need to calculate the first day of the quarter?
            format_string = "%%Y-%%m-01 00:00:00"
        if self.group_by == 'YEAR':
            format_string = "%%Y-01-01 00:00:00"
        return (format_string, f_type)

    def get_datetime_format(self):
        """
        Return the format for each grouped-by date entry. These are used on the x-axis of graphs.
        TODO: it might be useful to also allow a user-customizable formatting instead...
        """
        if self.group_by == 'MINUTE':
            return "%H:%M"
        elif self.group_by == 'HOUR':
            return "%H:00 %d %b"
        elif self.group_by == 'DAY':
            return "%d %b"
        elif self.group_by == 'DAYOFWEEK':
            return "%w"
        elif self.group_by == 'WEEK':
            return "%d %b %Y"
        elif self.group_by == 'MONTH':
            return "%b %Y"
        elif self.group_by == 'YEAR':
            return "%Y"
        elif self.group_by == 'QUARTER':
            return "%b %y"
        # Default when we don't do any grouping, HOUR:MINUTE DAY/MONTH
        return "%H:%M %d %b" 

    def get_tick_size_string(self):
        """
        Not used, could be when we need to specify the tickInterval. For now we let jqPlot handle the details.
        """
        if self.group_by == 'MINUTE':
            return '1 minute'
        elif self.group_by == 'HOUR':
            return '1 hour'
        elif self.group_by == 'DAY' or self.group_by == 'DAYOFWEEK':
            return '1 day'
        elif self.group_by == 'WEEK':
            return '7 day'
        elif self.group_by == 'MONTH':
            return '1 month'
        elif self.group_by == 'YEAR':
            return '1 year'
        elif self.group_by == 'QUARTER':
            return '3 month'
        return None
    
    def get_type(self):
        return "datetime"

class DataColumnInteger(DataColumn):
    max_value = models.IntegerField(blank = True, null = True)
    min_value = models.IntegerField(blank = True, null = True)
    group_by = models.BooleanField(default = False)

    def get_thresholds(self):
        return self.threshold_set.all()

    def get_group_by(self, force):
        if self.group_by or force:
            return "%s" % (self.name)
        return None

    def apply_filter(self):
        qs_filter = None
        if self.max_value != None:
            qs_filter = "%s__lte = %s" % (self.name, str(self.max_value))
        if self.min_value != None:
            if qs_filter:
                qs_filter += ", "
            qs_filter += "%s__gte = %s" % (self.name, str(self.min_value))
        return qs_filter
    
    def get_info(self):
        if self.min_value and self.max_value:
            return "Limited to all values between %s and %s" % (str(self.min_value), str(self.max_value))
        if self.min_value:
            return "Limited to a minimum of %s" % (str(self.min_value))
        if self.max_value:
            return "Limited to a maximum of  %s" % (str(self.min_value))            
        return ""

    def get_type(self):
        return "integer"

class DataColumnBoolean(DataColumn):
    max_value = models.IntegerField(blank = True, null = True)
    min_value = models.IntegerField(blank = True, null = True)
    group_by = models.BooleanField(default = False)
    name_true = models.CharField(max_length = global_max_length, blank = True, help_text = 'If used, shown when this field is True. By default "field_name" is used')
    name_false = models.CharField(max_length = global_max_length, blank = True, help_text = 'If used, shown when this field is False. By default "not field_name" is used')

    def get_thresholds(self):
        return self.threshold_set.all()

    def get_group_by(self, force):
        if self.group_by or force:
            return "%s" % (self.name)
        return None

    def get_name_true(self):
        if self.name_true != '':
            return self.name_true
        return self.name

    def get_name_false(self):
        if self.name_false != '':
            return self.name_false
        return 'not %s' % (self.name)

    def apply_filter(self):
        qs_filter = None
        if self.max_value != None:
            qs_filter = "%s__lte = %s" % (self.name, str(self.max_value))
        if self.min_value != None:
            if qs_filter:
                qs_filter += ", "
            qs_filter += "%s__gte = %s" % (self.name, str(self.min_value))
        return qs_filter
    
    def get_info(self):
        if self.min_value and self.max_value:
            return "Limited to all values between %s and %s" % (str(self.min_value), str(self.max_value))
        if self.min_value:
            return "Limited to a minimum of %s" % (str(self.min_value))
        if self.max_value:
            return "Limited to a maximum of  %s" % (str(self.min_value))            
        return ""

    def get_type(self):
        return "boolean"    

class DataColumnDecimal(DataColumn):
    max_value = models.DecimalField(max_digits = 50, decimal_places = 8, blank = True, null = True)
    min_value = models.DecimalField(max_digits = 50, decimal_places = 8, blank = True, null = True)
    group_by = models.BooleanField(default = False)

    def get_thresholds(self):
        return self.threshold_set.all()

    def get_group_by(self):
        if self.group_by:
            return "%s" % (self.name)
        return None

    def apply_filter(self):
        qs_filter = None
        if self.max_value != None:
            qs_filter = "%s__lt = %s" % (self.name, str(self.max_value))
        if self.min_value != None:
            if qs_filter:
                qs_filter += ", "
            qs_filter += "%s__gt = %s" % (self.name, str(self.min_value))
        return qs_filter

    def get_info(self):
        if self.min_value and self.max_value:
            return "Limited to all values between %s and %s" % (str(self.min_value), str(self.max_value))
        if self.min_value:
            return "Limited to a minimum of %s" % (str(self.min_value))
        if self.max_value:
            return "Limited to a maximum of  %s" % (str(self.min_value))            
        return ""

    def get_type(self):
        return "decimal"

class DataColumnString(DataColumn):
    limit_to = models.CharField(max_length = global_max_length, blank = True) # comma-separated list of allowed values
    group_by = models.BooleanField(default = False)

    def get_thresholds(self):
        return []

    def get_group_by(self, force = False):
        if self.group_by or force:
            return "%s" % (self.name)

    def apply_filter(self):
        qs_filter = None
        if self.limit_to != '':
            qs_filter = "%s__in = [%s]" % (self.name, self.limit_to)
        return qs_filter

    def get_info(self):
        if self.limit_to != '':
            return "Limited to the following fields: %s" % (self.limit_to)
        return ''

    def get_type(self):
        return "string"

class DataColumnFK(DataColumn):
    limit_to = models.CharField(max_length = global_max_length, blank = True) # comma-separated list of allowed values (ids)
    model = models.ForeignKey(DataModel)
    group_by = models.BooleanField(default = False)

    def get_thresholds(self):
        return []

    def get_data(self):
        model = self.get_model()
        return model.objects.all()

    def get_info(self):
        return unicode(self.model)

    def get_model(self):
        return get_model(self.selection.selected_model.app_name, self.model.model_name)

    def get_group_by(self, force = False):
        if self.group_by or force:
            return "%s_id" % (self.name)
        return None

    def apply_filter(self):
        qs_filter = None
        if self.limit_to:
            qs_filter = "%s__id__in = [%s]" % (self.name, self.limit_to)
        return qs_filter

    def get_type(self):
        return "foreign_key"

### Thresholds, probably suitable for a separate app ###


THRESHOLD_LEVELS = ( (0, 'Green'), (1, 'Yellow'), (2, 'Red') )

class ThresholdDecimal(models.Model):
    data_column = models.ForeignKey(DataColumnDecimal, related_name = 'threshold_set')
    thres_from = models.DecimalField(max_digits = 50, decimal_places = 8, blank = True, null = True)
    thres_to = models.DecimalField(max_digits = 50, decimal_places = 8, blank = True, null = True)
    thres_level = models.IntegerField(choices = THRESHOLD_LEVELS, default = 0)

    def get_dict(self):
        d = {'level': self.thres_level}
        if self.thres_from:
            d['from'] = self.thres_from
        if self.thres_to:
            d['to'] = self.thres_to
        return d

    def __unicode__(self):
        return "%s - level %d" % (self.data_column, self.thres_level) # for values between %d and %d" % (self.thres_level, self.thres_from, self.thresh_to)        

class ThresholdInteger(models.Model):
    data_column = models.ForeignKey(DataColumnInteger, related_name = 'threshold_set')
    thres_from = models.IntegerField(blank = True, null = True)
    thres_to = models.IntegerField(blank = True, null = True)
    thres_level = models.IntegerField(choices = THRESHOLD_LEVELS, default = 0)

    def get_dict(self):
        d = {'level': self.thres_level}
        if self.thres_from:
            d['from'] = self.thres_from
        if self.thres_to:
            d['to'] = self.thres_to
        return d

    def __unicode__(self):
        return "%s - level %d" % (self.data_column, self.thres_level) # for values between %d and %d" % (self.thres_level, self.thres_from, self.thresh_to)
