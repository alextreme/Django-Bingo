#!/usr/bin/python

from django.core.management import setup_environ
import settings
setup_environ(settings)
import time
import logging
import statgrab

from status.models import *

kb = 1024
mb = kb * kb

while True:
    ### Host data ###

    cpu = statgrab.sg_get_cpu_percents()
    load = statgrab.sg_get_load_stats()
    host = statgrab.sg_get_host_info()
    mem = statgrab.sg_get_mem_stats()
    hs = HostStats(hostname = host['hostname'], uptime = host['uptime'], arch = host['platform'], min1 = str(load['min1']), min5 = str(load['min5']), min15 = str(load['min15']), mem_total = mem['total'] / mb, mem_free = (mem['cache'] + mem['free']) / mb, mem_used = mem['used'] / mb)
    hs.save()
    ### FS data ###

    filesystems = statgrab.sg_get_fs_stats()
    for fs in filesystems:
        fs_stat = FilesystemStats(device = fs['device_name'], used_perc = str(float(fs['used']) / float(fs['size']) * 100.0), size = fs['size'] / mb, used = fs['used'] / mb,  avail = fs['avail'] / mb, fs_type = fs['fs_type'])
        fs_stat.save()
    ### Network data ###
    statgrab.sg_get_network_io_stats()
    time.sleep(1) # Collect data over 1 second
    diff = statgrab.sg_get_network_io_stats_diff()
    netstats = statgrab.sg_get_network_iface_stats()
    for iface in diff:
        for netstat in netstats:
            if iface['interface_name'] == netstat['interface_name']:
                ns = NetworkStats(interface = iface['interface_name'], up = netstat['up'], tx = iface['tx'] / kb, rx = iface['rx'] / kb)
                ns.save()
    time.sleep(1)
