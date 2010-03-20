from django import forms
from models import *
from querybuilder.models import *

class DashboardForm(forms.ModelForm):
    class Meta:
        model = Dashboard
        exclude = ('order', 'active',)

def get_element_form(element, data = None):
    if element.get_type() == 'table':
        return TableForm(data, instance = element)
    elif element.get_type() == 'graph':
        return GraphForm(data, instance = element)
    return ElementForm(data, instance = element)

class ElementForm(forms.ModelForm):
    class Meta:
        model = Element
        exclude = ('ordering', 'position', )

class GraphForm(forms.ModelForm):
    class Meta:
        model = Graph
        exclude = ('ordering', 'position', )

class TableForm(forms.ModelForm):
    class Meta:
        model = Table
        exclude = ('ordering', 'position', )

class TableColumnForm(forms.ModelForm):
    class Meta:
        model = TableColumn
        
