from django.shortcuts import get_object_or_404
from django.db import models
from querybuilder.models import DataSelection, DataColumn

import sys

global_max_length = 200
global_max_length_small = 40

DASHBOARD_LAYOUT_CHOICES = ( ('two-column', 'Two column layout'), ('three-column', 'Three column layout') )

class Dashboard(models.Model):
    name = models.CharField(max_length = global_max_length)
    layout = models.CharField(max_length = global_max_length_small, choices = DASHBOARD_LAYOUT_CHOICES, default = 'two-column')
    order = models.IntegerField(default = 0)
    active = models.BooleanField(default = True)

    class Meta:
        ordering = ["order"]

    def __unicode__(self):
        return self.name

    def get_total_elements(self):
        return self.element_related.all()

    def get_elements(self, column_name = None):
        if column_name:
            return self.element_related.filter(position = column_name).order_by('ordering')
        return self.element_related.filter(active = True)

    def get_element_width(self):
        if self.layout == 'two-column':
            return 580
        else:
            return 390

    def get_elements_left(self):
        return self.get_elements('left')

    def get_elements_middle(self):
        return self.get_elements('middle')

    def get_elements_right(self):
        return self.get_elements('right')

    def set_elements(self, element_id_list, column_name):
        elms = self.get_elements(column_name)
        for elm in elms:
            elm.position = ''
            elm.save()
            
        for i, elm_id in enumerate(element_id_list):
            element = get_object_or_404(Element, id = elm_id)
            element.position = column_name
            element.ordering = i
            element.save()
        return True

### Dashboard element models ###

def get_element_types():
    return {'graph': Graph,
            'table': Table}

class Element(models.Model):
    dashboard = models.ForeignKey(Dashboard, related_name = '%(class)s_related')
    name = models.CharField(max_length = global_max_length)
    position = models.CharField(max_length = global_max_length, choices = ( ('left', 'Left'), ('middle', 'Middle'), ('right', 'Right') ), default = 'left')
    ordering = models.IntegerField(default = 0)
    height = models.IntegerField(default = 0) # 0 = auto-expand?
    refresh_rate = models.IntegerField(default = 0) # 0 = Don't refresh
    active = models.BooleanField(default = True)

    def __unicode__(self):
        return "%s (%s / %d)" % (self.name, self.position, self.ordering)

    def get_child(self):
        """
        Return the sub-class / child of this Element. Currently rather messy...
        """
        try:
            if self.table:
                return self.table
        except:
            pass
        try:
            if self.graph:
                return self.graph
        except:
            pass
        return None

    def get_data_selections(self):
        """
        Return the data selections for this element.
        """
        child = self.get_child()
        if child:
            return child.data.all()
        return []

    def get_template_name(self):
        """
        Return the template file pathname, to be used to display this element.
        """
        elm_type = self.get_type()
        if elm_type != "Invalid":
            return "dashboard/elm_%s.html" % (elm_type)
        return None
    
    def get_type(self):
        """
        Return the type of sub-class / child this element represents.
        """
        child = self.get_child()
        if child:
            return child.get_type()
        return "Invalid"

GRAPH_TYPE_CHOICES = ( ('line', 'Line Graph'), ('linepoint', 'Line + Points Graph'), ('point', 'Point Graph'), ('bar', 'Bar Graph'), )

class Graph(Element):
    data = models.ManyToManyField(DataSelection)
    series = models.ForeignKey(DataColumn, related_name = 'series_graph_set', blank = True, null = True) # Use to place multiple graphs in one chart
    x_axis = models.ForeignKey(DataColumn, related_name = 'x_axis_graph_set', blank = True, null = True)
    y_axis = models.ForeignKey(DataColumn, related_name = 'y_axis_graph_set', blank = True, null = True)
    y_axis_from_zero = models.BooleanField("Start y-axis at 0?", default = 1)
    graph_type = models.CharField(max_length = global_max_length_small, choices = GRAPH_TYPE_CHOICES, default = 'line')
    fill = models.DecimalField(max_digits = 3, decimal_places = 2, blank = True, null = True, help_text = 'If non-empty, the shape will be filled with this value being the opacity of the area. Bars are always filled.')
    legend = models.BooleanField(default = True)
    count_series = models.BooleanField(default = False, help_text = 'Enable to simply plot the <b>number of entries</b> in the data selections. Implicitly done when assigning multiple data selections to a graph. Keep this off to plot the <b>data</b> from the data selection.')

    def show_points(self):
        if self.graph_type == 'linepoint' or self.graph_type == 'point':
            return True
        return False

    def show_lines(self):
        if self.graph_type == 'linepoint' or self.graph_type == 'line':
            return True
        return False

    def show_bars(self):
        if self.graph_type == 'bar':
            return True
        return False

    def get_type(self):
        return "graph"

    def get_series_objects(self):
        """
        In this bit we retrieve all id's from the QuerySet and retrieve the related models in bulk.
        Then we replace the series id's with the string representation of the related model instance.
        It's very messy, but I haven't found a simple way yet to do a values_list() while still automatically
        looking up the ForeignKey representation...
        """

        map_list = []
        if self.series and self.series.get_type() == 'foreign_key':
            series_model = self.series.get_child().get_model()
            for series in series_model.objects.all():
                abbr = unicode(series)
                if len(abbr) > 13:
                    abbr = abbr[0:10] + "..."
                map_list += [[series.id, unicode(series), abbr]]
        if self.series and self.series.get_type() == 'boolean':
            bool_column = self.series.get_child()
            map_list += [[0, bool_column.get_name_false(), bool_column.get_name_false() ]]
            map_list += [[1, bool_column.get_name_true(), bool_column.get_name_true() ]]
        return map_list

    def get_xaxis_ticks(self, data_qs):
        """
        Return the x-axis ticks as specified by the column's formatting.
        For non-datetime columns this isn't necessary.
        """
        x_axis_ticks = list(data_qs.distinct().values_list(self.x_axis.name, flat = True))
        labels = []
        if self.x_axis.get_type() == 'datetime' and self.x_axis.get_child().get_datetime_format():
            for tick in x_axis_ticks:
                try: # Format the datetime, else use the tick as a string
                    labels += [ tick.strftime(self.x_axis.get_child().get_datetime_format()) ]
                except:
                    labels += [ str(tick) ]
        else:
            labels = x_axis_ticks[:]
        return (x_axis_ticks, labels)

    def get_data_by_ticks(self, series_objects, empty_series, x_axis_ticks, data_list):
        """
        Format the data as required for a jqPlot barplot (optionally with categories).
        This data is matched against the x-axis ticks.
        """

        data_by_ticks = []
        neg_values = False
        non_integer = False
        for i, (s_id, s_name, s_abbreviation) in enumerate(series_objects): # Goal is a list of y-axis values grouped by the series for plotting via jqPlot's barplot
            data_elm = []
            zero_values = True
            for x in x_axis_ticks:
                curr_data_elm = False
                for l_elm in data_list:
                    if (empty_series or s_id == l_elm[1]) and x == l_elm[0]: # Same series, Same x_axis element
                        if not empty_series:
                            curr_data_elm = l_elm[2]
                        else:
                            curr_data_elm = l_elm[1]
                        if curr_data_elm < 0:
                            neg_values = True # If we have negative values, let the x_axis float
                        if curr_data_elm != 0:
                            zero_values = False
                        if type(curr_data_elm) != type(int()):
                            non_integer = True
                if not curr_data_elm:
                    curr_data_elm = 0
                data_elm += [curr_data_elm]

            if not zero_values:
                data_by_ticks += [data_elm]
            else:
                # We don't have any values for this series, or only 0-values. Ignore this series.
                del series_objects[i]
        return (series_objects, data_by_ticks, neg_values, non_integer)

    def get_data_by_xy(self, series_objects, empty_series, x_axis_ticks, data_list):
        """
        Format the data in a list of series, with each series containing a list of [x/y] values to plot.
        While we're at it, determine various states about the data that help us plot the data neatly.
        """

        data_by_xy = []
        neg_values = False
        non_integer = False
        
        for i, (s_id, s_name, s_abbreviation) in enumerate(series_objects): # Goal is a list of y-axis values grouped by the series for plotting via jqPlot's barplot
            data_elm = []
            zero_values = True

            for l_elm in data_list:
                if (empty_series or s_id == l_elm[1]):
                    if not empty_series:
                        curr_data_elm = [l_elm[0], l_elm[2]]
                    else:
                        curr_data_elm = [l_elm[0], l_elm[1]]
                    if curr_data_elm[1] < 0:
                        neg_values = True # If we have negative values, let the x_axis float
                    if curr_data_elm[1] != 0:
                        zero_values = False
                    if type(curr_data_elm[1]) != type(int()):
                        non_integer = True
                    
                    data_elm += [curr_data_elm]
                
            if not zero_values:
                data_by_xy += [data_elm]
            else:
                # We don't have any values for this series, or only 0-values. Ignore this series.
                del series_objects[i]
        return (series_objects, data_by_xy, neg_values, non_integer)

    def format_data(self, data_qs):
        """
        Given a data queryset, return the format as required by this Element subclass.

        In this case, format the data as required for the Graph. Formatting depends on the series and axis entered.
        """
        if len(data_qs) == 0:
            return []
        
        if len(data_qs) > 1 or self.count_series:
            # In all cases with multiple query sets, simply return the number of items in the query set.
            data_set = []
            count = 0
            labels = []
            for data_qs_elm in data_qs:
                count += 1
                label = data_qs_elm.model._meta.object_name
                if data_qs_elm.count_series_label:
                    labels += [data_qs_elm.count_series_label]
                else:
                    labels += [label]
                data_set +=  [ data_qs_elm.count() ]
            data_dict = { "data": [ data_set ],
                          "ticks": labels,
                          "series": None,
                          "empty_series": True,
                          "non_integer": False,
                          }
            return data_dict

        # We have a single query set, process it as usual
        data_qs = data_qs[0]


        # Determine the fields we need from the queryset
        field_names = []
        if self.x_axis:
            field_names += [self.x_axis.name]
        if self.series:
            field_names += [self.series.name]
        if self.y_axis:
            field_names += [self.y_axis.name]

        data_list = list(data_qs.values_list(*field_names)) # Unpack field names into separate arguments

        if self.x_axis:
            # Determine the ticks used on the x-axis        
            (x_axis_ticks, x_axis_labels) = self.get_xaxis_ticks(data_qs)
        else:
            x_axis_ticks = []
            x_axis_labels = []

        if self.series:
            series_objects = self.get_series_objects()
            empty_series = False
        else:
            series_objects = [ [0, 'values', 'values'], ]
            empty_series = True

        if self.graph_type == 'bar':
            (series_objects, transformed_data_list, neg_values, non_integer) = self.get_data_by_ticks(series_objects, empty_series, x_axis_ticks, data_list)
            x_axis_ticks = x_axis_labels
            # transformed_data_list example: [ [0, 14], [4, 13], [5, 16] ]
            # with as many list-elements as there are series, and with each list-element containing as many values as there are x-axis ticks
        else:
            (series_objects, transformed_data_list, neg_values, non_integer) = self.get_data_by_xy(series_objects, empty_series, x_axis_ticks, data_list)
            # transformed_data_list example: [ [ [ 1, 5], [2, 8], [3, 2] ], [ [ 1, 5], [2, 7], [3, 6] ] ]
            # with as many list-elements as there are series, with each list-element containing a list of 2 elements: the x and y values for this point
        
        series = []
        for s in series_objects: # jqPlot variables for the series
            d = { 'label': s[2] }
            if not self.show_lines() and not self.show_bars():
                d['showLine'] = False
            if not self.show_points() and not self.show_bars():
                d['showMarker'] = False
            series += [ d ]
        data_set = { 'data': transformed_data_list, 'ticks': x_axis_ticks, 'series': series, 'empty_series': empty_series, 'non_integer': non_integer}
        return data_set


TABLE_COLUMN_TYPE_CHOICES = ( ('text','Text'), ('line', 'Sparkline'), ('bar', 'Bar chart'), ('bullet', 'Bullet graph'), ('box', 'Box plot'), ('pie', 'Pie chart (brrr)') )

class TableColumn(models.Model):
    name = models.CharField(max_length = global_max_length)
    data_column = models.ForeignKey(DataColumn, related_name = 'table_column_data_set')
    element_type = models.CharField(max_length = global_max_length_small, choices = TABLE_COLUMN_TYPE_CHOICES)
    bar_width = models.IntegerField(default = 0, help_text = 'Width of each bar, in pixels. Only used when element type is "Bar chart", 0 = use default width.')

    def __unicode__(self):
        return u"%s (column: %s, type: %s)" % (self.name, self.data_column, self.element_type)

    def get_data(self, series_column, data_row, data_qs):
        data = None
        thresholds = None
        if self.data_column.get_thresholds():
            thresholds = []
            for threshold in self.data_column.get_thresholds():
                thresholds += [ threshold.get_dict() ]

        if self.element_type == 'text':
            name = self.data_column.name
            try:
                data = eval("str(data_row.%s)" % (name))
            except:
                data = ""
            data = { 'type': self.element_type, 'data': data }
        else:
            series_element = eval("data_row.%s" % ( series_column.name))
            try:
                eval_line = "data_qs.filter(%s = '%s')" % (series_column.name, series_element.id)
            except:
                eval_line = "data_qs.filter(%s = '%s')" % (series_column.name, series_element)
            data = eval(eval_line).values_list(self.data_column.name, flat = True)
            data = { 'type': self.element_type, 'data': data } # Wrap it up with the type name so we can format it correctly in the table
            if self.element_type == 'bar' and self.bar_width != 0:
                data['barWidth'] = self.bar_width
            
        if thresholds:
            data['thresholds'] = thresholds
        return data

class Table(Element):
    data = models.ManyToManyField(DataSelection)
    series = models.ForeignKey(DataColumn, related_name = 'series_table_set', blank = True, null = True)
    column_elements = models.ManyToManyField(TableColumn, related_name = 'column_elements_table_set', blank = True, null = True)
    count_series = models.BooleanField(default = False, help_text = 'Enable to simply plot the <b>number of entries</b> in the data selections. Implicitly done when assigning multiple data selections to a table. Keep this off to plot the <b>data</b> from the data selection.')

    def get_data_column_elements(self):
        return DataColumn.objects.filter(id__in = self.column_elements.values_list('data_column'))
    
    def get_type(self):
        return "table"

    def format_data(self, data_qs):
        """
        Format the given query set according to this table layout.

        The returned format is a list of rows, with each row containing a as many data elements as there are columns defined.

        Each data element is either a string (default) or a dictionary with both 'type' and 'data' values set.
        """
        data_list = []

        if len(data_qs) == 0:
            return data_list
        
        if len(data_qs) > 1 or self.count_series:
            # In all cases with multiple query sets, simply return the number of items in the query set.
            data_set = []
            for data_qs_elm in data_qs:
                label = data_qs_elm.model._meta.object_name
                if data_qs_elm.count_series_label:
                    label = data_qs_elm.count_series_label
                    
                data_set += [[{ 'data': label, 'type': 'text' }, {'data': data_qs_elm.count(), 'type': 'text'}]]
            return data_set

        # A single queryset, proceed as normal
        data_qs = data_qs[0]
        
        columns = self.column_elements.all()
        grouped_data_qs = data_qs.all() # Make a copy. The raw QS is given to each data element, the grouped version is used for each row.
        grouped_data_qs.query.group_by = [self.series.get_group_by(force = True)]
        for data_row in grouped_data_qs:
            row = []
            for column in columns:
                data = column.get_data(self.series, data_row, data_qs)
                row += [ data ]
            data_list += [ row ]
        return data_list

    def prepopulate_tablecolumns(self):
        for data in self.data.all():
            for column in data.get_columns():
                pass # TODO: Implement this, if necessary

    def save(self, *args, **kwargs):
        """
        When saving a new Table, initialize it with all columns for the data selection linked (if any are given)
        """

        new_obj = False
        try:
            old_instance = Table.objects.get(pk = self.pk)
        except Exception, e:
            # Couldn't find the old instance, this must be a new assessment
            new_obj = True
                                                    
        super(Table, self).save(*args, **kwargs)

        if new_obj and self.data.all().count() != 0 and self.column_elements.all().count() == 0:
            pass # We don't do anything for now!
        super(Table, self).save(*args, **kwargs)
