from django.db import models

global_max_length = 200

class FilesystemStats(models.Model):
    device = models.CharField(max_length = global_max_length)
    used_perc = models.DecimalField(max_digits = 5, decimal_places = 2)
    size = models.IntegerField()
    used = models.IntegerField()
    avail = models.IntegerField()
    fs_type = models.CharField(max_length = global_max_length)
    at = models.DateTimeField(auto_now_add = True)

class NetworkStats(models.Model):
    interface = models.CharField(max_length = global_max_length)
    up = models.BooleanField(default = 0)
    tx = models.IntegerField()
    rx = models.IntegerField()
    at = models.DateTimeField(auto_now_add = True)

class HostStats(models.Model):
    hostname = models.CharField(max_length = global_max_length)
    uptime = models.IntegerField()
    arch = models.CharField(max_length = global_max_length)
    
    min1 = models.DecimalField(max_digits = 5, decimal_places = 2)
    min5 = models.DecimalField(max_digits = 5, decimal_places = 2)
    min15 = models.DecimalField(max_digits = 5, decimal_places = 2)    

    mem_total = models.IntegerField()
    mem_free = models.IntegerField()
    mem_used = models.IntegerField()
    
    at = models.DateTimeField(auto_now_add = True)
