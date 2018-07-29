import urllib
import logging

log = logging.getLogger("GomBot")


class Plexmediaserver():
    # LD_LIBRARY_PATH=/usr/lib/plexmediaserver
    # curl http://192.168.0.20:32400/library/sections/2/refresh
    host = ''
    port = ''

    def __init__(selfself):
        log.debug("plex init")

    def refresh(self, section_id):
        try:
            refresh_url = "http://%s:%s/library/sections/%s/refresh" % (self.host, self.port, section_id)
            log.debug("Plex Media Server - %d refresh", section_id)
            log.debug(refresh_url)
            f = urllib.request.urlopen(refresh_url)
            return True
        except:
            return False
