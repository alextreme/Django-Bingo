#!/usr/bin/python

from django.core.management import setup_environ
import settings
setup_environ(settings)
import time
import ping.ping as pinger
import logging

from ping.models import PingHost, PingResult

while True:
    ping_hosts = PingHost.objects.filter(active = True)
    time.sleep(5)    
    for ping_host in ping_hosts:
        logging.debug(u"Pinging: " + ping_host.hostname)
        result = pinger.ping(ping_host.hostname)
        if result != False:
            logging.debug(u"Ping success:")
            logging.debug(result)
            p_result = PingResult(min_delay = result[0], avg_delay = result[1], max_delay = result[2], stddev = result[3])
            p_result.host = ping_host
            p_result.save()
        else:
            logging.debug(u"Ping failed!")
        time.sleep(2)
