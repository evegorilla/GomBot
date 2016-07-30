#!/usr/bin/env python3.5
#-*- coding: utf-8 -*-

import telepot
import time
import logging
import json
import pprint
import feedparser
import urllib
import sys
from _ctypes import Array
#reload(sys)
#sys.setdefaultencoding('utf-8')

class GomBot(telepot.Bot):
	token=''
	admin_id=[]
	public_room=[]
	menu = {}

	def __init__(self):
		self.stdin_path = '/dev/null'
		self.stdout_path = '/dev/tty'
		self.stderr_path = '/dev/tty'
		self.pidfile_path =  '/var/run/gombot.pid'
		self.pidfile_timeout = 5
		super(GomBot, self).__init__(self.token)
		self._answerer = telepot.helper.Answerer(self)

	def run(self):
		try:
			self.message_loop(self.handle)
			log.debug('Listening ...')
			while 1:
				tc = Transmission()
				arr = Transmission.garbage_collection(tc)
				
				if len(arr)>0: #노티할애가 있으면
					pms = Plexmediaserver()
					if not pms.refresh(2):
						log.debug("refresh 실패로 완료된 시드유지함")
						return
					str = "\n".join(arr)
					for room in self.public_room:	
						self.sendMessage(room, "%s\n 준비되었습니다."%str)
	
				time.sleep(10)
		except Exception as e:
			log.exception("Main loop error")

	def handle(self, msg):
		flavor = 'normal'
		# normal message
		if flavor == 'normal':
			content_type, chat_type, chat_id = telepot.glance(msg)
			log.info('Normal Message:%s %s %s', content_type, chat_type, chat_id)
			log.debug(json.dumps(msg, ensure_ascii=False))
			command = msg['text']
			from_id = msg['from']['id']
			chat_id = msg['chat']['id'] 
			log.debug(command)
			
			if not command.startswith('/'): # 명령커맨드일 경우
				return
			
			keyword = command[1:].split(' ')
			
			if keyword[0] == "셧다운":
				log.debug("셧다운 권한확인")
				if from_id in self.admin_id:
					self.sendMessage(chat_id,"모든 서버를 셧다운 합니다.")
				else:
					log.debug(" 권한 없는 사용자(%d)가 셧다운 시도" % from_id)
					self.sendMessage(chat_id,"권한이 없습니다.")
			elif keyword[0] == "하이":
				self.sendMessage(chat_id,"반갑구만 반가워요")
					
			elif keyword[0] == "검색": # 토렌트 검색해야지
				if chat_id in self.public_room: # 채팅방이 공방이면
					self.sendMessage(chat_id, "공개방입니다.\n 봇을 따로 소환해 검색하세요")
					return

				result = self.get_search_list(' '.join(keyword[1:]))
				self.set_menu(chat_id, from_id,result)
								
			elif keyword[0] == '받기': # 토렌트 검색해야지
				idx = int(keyword[1].split('.')[0]) - 1
				menu = self.menu[chat_id][idx]
				log.debug("다운로드주소 : %s" % menu['link'])
				
				tc = Transmission()
				dn_path = tc.get_dnpath(menu['title'])
				log.debug ("title: %s "% menu['title'])
				log.debug ("link: %s "% menu['link'])
				log.debug ("다운로드경로는 %s" % dn_path)
				to = tc.add_torrent(menu['link'],download_dir=dn_path)
				
				if (to):
					log.debug("downloading : %s %s" % (to.id, to.name))
					self.sendMessage(chat_id,'%s 다운로딩' % menu['title'])
				else:
					self.sendMessage(chat_id,'다운로드 실패')
			
			elif keyword[0] == '확인': # 토렌트 진행상황 확인
				tc = Transmission()
				torrents = tc.get_torrents()
			
				if len(torrents) == 0:
					self.sendMessage(chat_id, "다운로드중인 파일은 없습니다.")
					return
				
				str = ''
				for torrent in torrents:
					str = str + "%s - %s peers %.2f %%\n" % (torrent.name[:20],torrent.peersConnected, torrent.percentDone*100)
				self.sendMessage(chat_id, str)
			elif keyword[0] == "갱신":
				pms = Plexmediaserver()
				arr = [1,2]
				for num in arr:
					pms.refresh(num)
			else:
				str = {"/검색 [검색어] - 검색어를 토렌트사이트에서 검색합니다.",
					   "/확인 - 토렌트 다운로드 진행상황을 확인합니다.",
					   "/갱신 - Plex Media Server 라이브러리를 갱신합니다."}
				str = "\n".join(str)
				self.sendMessage(chat_id,str)
					   
		# inline query - need `/setinline`
		elif flavor == 'inline_query':
			query_id, from_id, query_string = telepot.glance(msg, flavor=flavor)
			print('Inline Query:', query_id, from_id, query_string)

			def compute_answer():
				# Compose your own answers
				articles = [{'type': 'article',
								'id': 'abc', 'title': query_string, 'message_text': query_string}]

				return articles

			self._answerer.answer(msg, compute_answer)

		# chosen inline result - need `/setinlinefeedback`
		elif flavor == 'chosen_inline_result':
			result_id, from_id, query_string = telepot.glance(msg, flavor=flavor)
			print('Chosen Inline Result:', result_id, from_id, query_string)

			# Remember the chosen answer to do better next time

		#else:
		#	raise telepot.BadFlavor(msg)
	
	def get_search_list(self, keyword):
		from bs4 import BeautifulSoup
		import urllib.request
		log.debug(keyword)
		url = Transmission.url % urllib.request.quote(keyword)
		headers = { 'User-Agent' : 'Mozilla/5.0' }
		req = urllib.request.Request(url, None, headers)
		handle = urllib.request.urlopen(req)

		data = handle.read()
		soup = BeautifulSoup(data,"lxml")

		count = 0
		
		
		arrData = []
		for item in soup.findAll("item"):
			count = count + 1
			if (count>10):
				break
			
			arr = {}
			arr['title'] = item.title.next_element
			arr['link'] = item.link.next_element
			log.debug("%d 제목 : %s" % (count,arr['title']))
			arrData.append(arr)
				
		return arrData
	
	def set_menu(self,chat_id, from_id, searchresult):
		self.menu[chat_id] = []
		
		for (i,entry) in enumerate(searchresult):
			arr = {}
			arr['title'] = entry['title']
			arr['link'] = entry['link']
			
			self.menu[chat_id].append(arr)
		
		self.set_keyboard(chat_id, searchresult)
		
	def set_keyboard(self,chat_id, searchresult):
		output_list =[]
		
		for (i,entry) in enumerate(searchresult):
			title = "/받기 " + str(i+1) + ". " + entry['title']
			temp_list = []
			temp_list.append(title[:50])
			log.debug(title)
			output_list.append(temp_list)
			
		show_keyboard = {'keyboard': output_list}
		self.sendMessage(chat_id,'선택해주세요',reply_markup=show_keyboard)


		
		
class Plexmediaserver():
	#LD_LIBRARY_PATH=/usr/lib/plexmediaserver
	#curl http://192.168.0.20:32400/library/sections/2/refresh
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
		
import transmissionrpc
class Transmission(transmissionrpc.Client):
	shost = ''
	sport = ''
	uname = ''
	upass = ''
	url = ''
	mediapath = ''
	tvdir = ''
	moviedir=''
	tc = ''

	def __init__(self):
		super(Transmission, self).__init__(self.shost, self.sport, self.uname,self.upass)
	
	def garbage_collection(self):
		torrents = self.get_torrents()
		
		arr = []
		for torrent in torrents:
			if torrent.percentDone == 1: # Downloaded
				self.remove_torrent(torrent.id)
				log.debug("Downloaded - %d %s"%(torrent.id, torrent.name))
				ext_str = torrent.downloadDir.replace(self.mediapath,'')
				arr.append("%s (%s)"%(torrent.name,ext_str))
		return arr
	
	def get_dir(self):
		import os
		list = os.listdir(self.mediapath+self.tvdir)
		log.debug(json.dumps(list, ensure_ascii=False))
		return list

	def get_dnpath(self, filename):
		title = filename.split('.')[0]
		log.debug(title +" 제목을  기준으로 확인중")
		list = self.get_dir()

		found = False
		for n in list:
			if n.replace(' ','') in title.replace(' ',''):
				#문자열이 존재하면
				dn_dir = self.mediapath+self.tvdir+"/"+n+"/"
				log.info("기존 디렉토리 찾음 " + n)
				return dn_dir

		if (self.is_tv(title)):
			# TV구만
			dn_dir =  self.mediapath+self.tvdir+"/"+title+"/"
		else:
			# 영화라 치자
			dn_dir =  self.mediapath+self.moviedir+"/"+title+"/"

		log.info(dn_dir+"에 다운로드 합니다.")
		return dn_dir

	def is_tv(self,title):
		found = False
		list = self.get_dir()


		if  (not found):
			log.debug("_"+title + "_ TVDB를 참조합니다.")
			# TV프로그램인지 확인해보자
			import urllib
			
			import xml.etree.ElementTree as ET
			
			TVDB_TITLE='http://thetvdb.com/api/GetSeries.php?seriesname=%s&language=ko'

			url = TVDB_TITLE % (urllib.parse.quote(title))
			rss = ET.parse(urllib.request.urlopen(url)).getroot()

			seriesid = -1
			for element in rss.findall("Series"):
				seriesid = element.findtext("seriesid")
				dn_dir = self.mediapath+self.tvdir+"/"+title+"/"
				log.debug(dn_dir)
			if (seriesid != -1):
				found = True
			else:
				log.debug("찾지 못했습니다." + url)
		return  found

def loadConf():
	fp = open(conf_file,'r')
	conf = json.loads(fp.read())
	fp.close()

	GomBot.token = conf['telegram']['token']
	GomBot.admin_id = conf['telegram']['admin_id']
	GomBot.public_room = conf['telegram']['public_room']

	Transmission.shost = conf['transmission']['host']
	Transmission.sport = conf['transmission']['port']
	Transmission.uname = conf['transmission']['user']
	Transmission.upass = conf['transmission']['pass']
	Transmission.url = conf['transmission']['url']
	Transmission.mediapath = conf['transmission']['mediapath']
	Transmission.tvdir = conf['transmission']['tvdir']
	Transmission.moviedir = conf['transmission']['moviedir']
	Plexmediaserver.host = conf['plexmediaserver']['host']
	Plexmediaserver.port = conf['plexmediaserver']['port']
	
import time
from daemon import runner # python-daemon2
import logging.handlers
#load configuration
conf_file = 'gombot-settings.json'
loadConf()

bot = GomBot()

log = logging.getLogger("GomBot")
log.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(name)s:%(levelname)s %(message)s (%(filename)s:%(lineno)s)",
							datefmt='%Y-%m-%d %H:%M:%S')
handler = logging.handlers.RotatingFileHandler("GomBot.log", maxBytes=10240, backupCount=1)
handler.setFormatter(formatter)
handler2 = logging.StreamHandler()
handler2.setFormatter(formatter)
log.addHandler(handler)
log.addHandler(handler2)

if (len(sys.argv)>1 and sys.argv[1] == "foreground"):
	log.info("Foreground mode start")
	log.setLevel(logging.DEBUG)
	log.debug("Debug mode setted.")
	bot.run()
	exit()

daemon_runner = runner.DaemonRunner(bot)
daemon_runner.daemon_context.files_preserve=[handler.stream]
daemon_runner.do_action()
