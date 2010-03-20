from django import forms
from models import *

import views

def get_column_form(column, data = None):
    if column.get_type() == 'integer':
        return DataColumnIntegerForm(data, instance = column)
    elif column.get_type() == 'boolean':
        return DataColumnBooleanForm(data, instance = column)
    elif column.get_type() == 'decimal':
        return DataColumnDecimalForm(data, instance = column)
    elif column.get_type() == 'string':
        return DataColumnStringForm(data, instance = column)
    elif column.get_type() == 'datetime':
        return DataColumnDateTimeForm(data, instance = column)
    elif column.get_type() == 'foreign_key':
        return DataColumnFKForm(data, instance = column)
    # Return generic DCForm
    return DataColumnForm(data, instance = column)

class DataSelectionForm(forms.ModelForm):
    class Meta:
        model = DataSelection

class DataColumnForm(forms.ModelForm):
    class Meta:
        model = DataColumn

class DataColumnIntegerForm(forms.ModelForm):
    class Meta:
        model = DataColumnInteger

class DataColumnBooleanForm(forms.ModelForm):
    class Meta:
        model = DataColumnBoolean

class DataColumnDecimalForm(forms.ModelForm):
    class Meta:
        model = DataColumnDecimal

class DataColumnStringForm(forms.ModelForm):
    class Meta:
        model = DataColumnString

class DataColumnDateTimeForm(forms.ModelForm):
    class Meta:
        model = DataColumnDateTime

class DataColumnFKForm(forms.ModelForm):
    class Meta:
        model = DataColumnFK

class AddSelectionStep1Form(forms.ModelForm):
    app_name = forms.ChoiceField(choices = get_apps_tuple())
    
    class Meta:
        model = DataSelection
        fields = ('name', )

class AddSelectionStep2Form(forms.ModelForm):
    class Meta:
        model = DataSelection
        fields = ('selected_model', 'auto_add_columns',)

from django.contrib.formtools.wizard import FormWizard

class AddSelectionWizard(FormWizard):
    def get_template(self, step):
        return 'querybuilder/add_selection.html'
    
    def process_step(self, request, form, step):
        if form.is_valid() and step == 0: # Process the application, add all models found
            add_models_from_app(form.cleaned_data['app_name'])

    def done(self, request, form_list):
        instance = None
        for form in form_list:
            if instance != None:
                form.instance = instance
            instance = form.save()
        return views.redirect_to_index()
