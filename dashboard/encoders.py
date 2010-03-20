from django.utils import simplejson
import datetime
import decimal

class GraphEncoder(simplejson.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")
#            return int(time.mktime(o.timetuple())) # Return as timestamp
#            return o.strftime("%Y-%m-%d %H:%M")        
        if isinstance(o, decimal.Decimal):
            return float(o)
        return simplejson.JSONEncoder.default(self, o)

class TableEncoder(simplejson.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return str(o)
        if isinstance(o, decimal.Decimal):
            return str(round(o, 3))
        try:
            return simplejson.JSONEncoder.default(self, o)
        except TypeError, x: # Attempt to encode any lists with objects unencodable by the default JsonEncoder (ie. the above)
            try:
                return list(o)
            except:
                return x

json_table_encoder = TableEncoder()
json_graph_encoder = GraphEncoder()
