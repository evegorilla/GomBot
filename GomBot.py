#!/usr/local/bin/python2
#-*- coding: utf-8 -*-

import telepot
import time
import logging
import json
import pprint
import feedparser
import urllib
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

logging.basicConfig(level=logging.DEBUG)
conf_file = 'gombot-settings.json'

class GomBot(telepot.Bot):
	token=''
	admin_id=[]
	public_room=[]
	READY="토렌트 다운로드"
	menu = ''

	def __init__(self):
		self.stdin_path = '/dev/null'
		self.stdout_path = '/dev/tty'
		self.stderr_path = '/dev/tty'
		self.pidfile_path =  '/var/run/gombot.pid'
		self.pidfile_timeout = 5
		super(GomBot, self).__init__(self.token)
		self._answerer = telepot.helper.Answerer(self)

	def run(self):
		self.notifyOnMessage()
		print('Listening ...')
		while 1:
			time.sleep(10)
		
	def handle(self, msg):
		flavor = telepot.flavor(msg)

		# normal message
		if flavor == 'normal':
			content_type, chat_type, chat_id = telepot.glance(msg)
			print('Normal Message:', content_type, chat_type, chat_id)
			logging.debug(json.dumps(msg, ensure_ascii=False))
			command = msg['text'].encode('utf-8')
			from_id = str(msg['from']['id'])
			chat_id = msg['chat']['id'] 
			
			if command == "/셧다운":
				logging.debug("셧다운 권한확인")
				if str(from_id) in self.admin_id:
					self.sendMessage(chat_id,"모든 서버를 셧다운 합니다.")
				else:
					logging.debug(from_id+ " 권한 없는 사용자가 셧다운 시도")
					self.sendMessage(chat_id,"권한이 없습니다.")
			elif command == '/하이':
				self.sendMessage(chat_id,"반갑구만 반가워요")
			elif command.startswith("/검색"): # 토렌트 검색해야지
				if chat_id in self.public_room: # 채팅방이 공방이면
					self.sendMessage(chat_id, "공개방입니다.\n 봇을 따로 소환해 검색하세요")
					return
				
				keyword = command[8:]
				url = "https://torrentkim3.net/bbs/rss.php?k=%s"%(urllib.quote(keyword))

				logging.debug(keyword + " " + url)
				self.menu = feedparser.parse(url)

				output_list =[]
				for (i,entry) in enumerate(self.menu.entries):
					if i == 10: break
					title = str(i+1) + ". " + entry.title

					temp_list = []
					temp_list.append(title[:50])
					logging.debug(title)
					output_list.append(temp_list)


				show_keyboard = {'keyboard': output_list}
				self.sendMessage(chat_id,'선택해주세요',reply_markup=show_keyboard)
				self.mode=self.READY

			elif (self.mode==self.READY): #다운로드시작
				self.mode=''
				index = int(command.split('.')[0]) - 1
				magnet = self.menu.entries[index].link
				title = str(self.menu.entries[index].title)
				logging.debug("제목은 "+title)
				tc = Transmission()
				dn_path = tc.get_dnpath(title)
				#print ("link: ", magnet)
				logging.debug ("다운로드경로는 " + dn_path)
				to = tc.add_torrent(magnet,download_dir=dn_path)
				if (to):
					self.sendMessage(chat_id,'다운로드가 시작되었습니다.')
					print(to.name + " ")
					i = 0
					for item in tc.get_torrents():
						i=i+1	
						print(item[i].name)

				else:
					self.sendMessage(chat_id,'다운로드 실패')
				

			# Do your stuff according to `content_type` ...

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

		else:
			raise telepot.BadFlavor(msg)

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
		logging.debug(self.shost + " ")
		logging.debug(self.sport)
		logging.debug(self.uname + " " + self.upass)
		super(Transmission, self).__init__(self.shost, self.sport, self.uname,self.upass)

	
	def get_dir(self):
		import os
		list = os.listdir(self.mediapath+self.tvdir)
		logging.debug(json.dumps(list, ensure_ascii=False))
		return list

	def get_dnpath(self, filename):
		title = filename.split('.')[0]
		logging.debug(title +" 제목을  기준으로 확인중")
		list = self.get_dir()

		found = False
		for n in list:
			if n in title:
				#문자열이 존재하면
				dn_dir = self.mediapath+self.tvdir+"/"+n+"/"
				logging.info("기존 디렉토리 찾음 " + n)
				return dn_dir

		if (self.is_tv(title)):
			# TV구만
			dn_dir =  self.mediapath+self.tvdir+"/"+title+"/"
		else:
			# 영화라 치자
			dn_dir =  self.mediapath+self.moviedir+"/"+title+"/"

		logging.debug(dn_dir+"로 결정")
		return dn_dir

	def is_tv(self,title):
		found = False
		list = self.get_dir()


		if  (not found):
			logging.info("_"+title + "_ TVDB를 참조합니다.")
			# TV프로그램인지 확인해보자
			import urllib
			import xml.etree.ElementTree as ET

			TVDB_TITLE='http://thetvdb.com/api/GetSeries.php?seriesname=%s&language=ko'

			url = TVDB_TITLE % (urllib.quote(title))
			rss = ET.parse(urllib.urlopen(url)).getroot()

			seriesid = -1
			for element in rss.findall("Series"):
				seriesid = element.findtext("seriesid")
				dn_dir = self.mediapath+self.tvdir+"/"+title+"/"
				logging.debug(dn_dir)
			if (seriesid != -1):
				found = True
			else:
				logging.info("찾지 못했습니다." + url)
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

import logging
import time
from daemon import runner # python-daemon

loadConf()

bot = GomBot()
logger = logging.getLogger("DaemonLog")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.FileHandler("./GomBot.log")
handler.setFormatter(formatter)
logger.addHandler(handler)
daemon_runner = runner.DaemonRunner(bot)
daemon_runner.daemon_context.files_preserve=[handler.stream]
daemon_runner.do_action()
