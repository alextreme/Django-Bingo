from django.db import models

global_max_length = 200

class PingHost(models.Model):
    hostname = models.CharField(max_length = global_max_length)
    active = models.BooleanField(default = True)

    def __unicode__(self):
        return self.hostname

class PingResult(models.Model):
    host = models.ForeignKey(PingHost)
    min_delay = models.DecimalField(max_digits = 10, decimal_places = 3)
    avg_delay = models.DecimalField(max_digits = 10, decimal_places = 3)
    max_delay = models.DecimalField(max_digits = 10, decimal_places = 3)    
    stddev = models.DecimalField(max_digits = 10, decimal_places = 3)
    at = models.DateTimeField(auto_now_add = True)

    def __unicode__(self):
        return unicode(self.host) + u" " + str(self.avg_delay) + " at " + str(self.at)

