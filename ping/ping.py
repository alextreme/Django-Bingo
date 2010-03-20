import subprocess
import re

def ping(hostname):
    ping = subprocess.Popen(
        ["ping", "-c", "4", hostname],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE
        )

    out, error = ping.communicate()
    matcher = re.compile("rtt min/avg/max/mdev = (\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)")
    try:
        return matcher.search(out).groups()
    except:
        return False
