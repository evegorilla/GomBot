GomBot
======

컨셉
-------
곰봇은 텔레그램API를 통해 서버를 제어하는 프로그램입니다. 
지금은 토렌트 검색과 다운로드 기능만 지원합니다.


사전준비
-------
pkg install python35
python35 -m ensurepip
pip3 install --upgrade pip
pip3 install telepot feedparser transmissionrpc python-daemon

사용방법
>실행
>>python GomBot.py start
>중지
>>python GomBot.py stop
>재시작
>>python GomBot.py restart

사용방법
> /검색 태양의 후회 => 토렌트사이트에서 "태양의 후회"에 대해 검색하여 결과를 전송