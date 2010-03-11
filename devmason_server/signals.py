import telnetlib
import sys

from django.db.models.signals import post_save
from devmason_server.models import Build

pw = "devmason_roxx"
srv = "irc.freenode.net"
chan = "#devmason"

def send_irc_msg(msg):
    try:
        t = telnetlib.Telnet()
        t.open('10.177.22.217', port=13337)
        t.write('%s %s&%s&%s\n' % (pw, srv, chan, msg))
    except:
        pass

def irc_handler(sender, **kwargs):
    build = kwargs['instance']
    send_irc_msg('%s: http://devmason.com%s | Passed: %s' % (build, build.get_absolute_url(), build.success))

post_save.connect(irc_handler, sender=Build)
