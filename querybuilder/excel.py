#
# Convert a QuerySet into an Excel file using xlwt (if installed)
# This was converted from an earlier project and was written by Brendan Sleight.
#

import tempfile
from django.http import HttpResponse
from datetime import datetime

def get_workbook():
    import xlwt
    return xlwt.Workbook()

def get_excel_data_from_wb(wb):
    """
    Return the Excel data from a xlst Workbook.
    """
    tmp = tempfile.NamedTemporaryFile()
    wb.save(tmp.name)
    f = open(tmp.name, "rb")
    xls_data = f.read()
    f.close()
    return xls_data

def response_excel_from_wb(wb, fname="DataSelection.xls"):
    """
    Return a HttpResponse with an Excel-file generated from the given xlst Workbook.
    Modify fname to change the filename used.
    """
    
    xls_data = get_excel_data_from_wb(wb)
    response = HttpResponse(xls_data, mimetype='application/vnd.ms-excel')
    filename = 'attachment; filename=' + fname
    response['Content-Disposition'] = filename
    return response

def queryset_to_xls(qs, data_selection, xls_name = 'Data'):
    import xlwt
    wb = xlwt.Workbook()
    export_as_work_sheet(qs, wb, xls_name, data_selection)
    data = get_excel_data_from_wb(wb)
    return response_excel_from_wb(wb)

def export_as_work_sheet(qs, workbook, worksheetName, data_selection):
    import xlwt
    ws = workbook.add_sheet(worksheetName)
        
    styleDateTime = xlwt.XFStyle()
    styleDateTime.num_format_str = 'DD/MM/YYYY HH:MM:SS'
    stylePlain = xlwt.XFStyle()
    y = 0
    x = 0

    for obj in qs:
        for column in data_selection.get_columns():
            elm = getattr(obj, column.name)
            if column.get_type() == 'datetime':
                s = styleDateTime
            else:
                s = stylePlain
            try:
                ws.write(y, x, str(elm), s)
            except:
                ws.write(y, x, str("(Invalid data)"), s)
            x = x + 1
        x = 0
        y = y + 1
