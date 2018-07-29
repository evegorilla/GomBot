import transmissionrpc
import logging

log = logging.getLogger("GomBot")


class Transmission(transmissionrpc.Client):
    shost = ''
    sport = ''
    uname = ''
    upass = ''
    url = 'https://torrenthaja.com/bbs/search.php?search_flag=search&stx=%s'
    mediapath = ''
    tvdir = ''
    moviedir = ''
    tc = ''

    def __init__(self):
        super(Transmission, self).__init__(self.shost, self.sport, self.uname, self.upass)

    def garbage_collection(self):
        torrents = self.get_torrents()

        arr = []
        for torrent in torrents:
            if torrent.percentDone == 1:  # Downloaded
                self.remove_torrent(torrent.id)
                log.debug("Downloaded - %d %s" % (torrent.id, torrent.name))
                ext_str = torrent.downloadDir.replace(self.mediapath, '')
                arr.append("%s (%s)" % (torrent.name, ext_str))
        return arr

    def get_dir(self):
        import os
        list = os.listdir(self.mediapath + self.tvdir)
        log.debug(json.dumps(list, ensure_ascii=False))
        return list

    def get_dnpath(self, filename):
        title = filename.split('.')[0]
        log.debug(title + " 제목을  기준으로 확인중")
        list = self.get_dir()

        found = False
        for n in list:
            if n.replace(' ', '') in title.replace(' ', ''):
                # 문자열이 존재하면
                dn_dir = self.mediapath + self.tvdir + "/" + n + "/"
                log.info("기존 디렉토리 찾음 " + n)
                return dn_dir

        if (self.is_tv(title)):
            # TV구만
            dn_dir = self.mediapath + self.tvdir + "/" + title + "/"
        else:
            # 영화라 치자
            # dn_dir =  self.mediapath+self.moviedir+"/"+title+"/"
            dn_dir = self.mediapath + self.tvdir + "/" + title + "/"

        log.info(dn_dir + "에 다운로드 합니다.")
        return dn_dir

    def is_tv(self, title):
        found = False
        list = self.get_dir()

        if (not found):
            log.debug("_" + title + "_ TVDB를 참조합니다.")
            # TV프로그램인지 확인해보자
            import urllib

            import xml.etree.ElementTree as ET

            TVDB_TITLE = 'http://thetvdb.com/api/GetSeries.php?seriesname=%s&language=ko'

            url = TVDB_TITLE % (urllib.parse.quote(title))
            rss = ET.parse(urllib.request.urlopen(url)).getroot()

            seriesid = -1
            for element in rss.findall("Series"):
                seriesid = element.findtext("seriesid")
                dn_dir = self.mediapath + self.tvdir + "/" + title + "/"
                log.debug(dn_dir)
            if (seriesid != -1):
                found = True
            else:
                log.debug("찾지 못했습니다." + url)
        return found

