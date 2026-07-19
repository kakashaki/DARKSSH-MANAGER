#!/usr/bin/env python3
# encoding: utf-8
# DARKSSH By @Crazy_vpn
import sys
from os import system
from proxy_common import run_server
system("clear")
#conexao
IP = '0.0.0.0'
try:
   PORT = int(sys.argv[1])
except:
   PORT = 80
PASS = ''
BUFLEN = 8196 * 8
TIMEOUT = 60
MSG = 'DARKSSH'
COR = '<font color="null">'
FTAG = '</font>'
DEFAULT_HOST = '0.0.0.0:22'
RESPONSE = "HTTP/1.1 200 " + str(COR) + str(MSG) + str(FTAG) + "\r\n\r\n"

if __name__ == '__main__':
    run_server(IP, PORT, BUFLEN, TIMEOUT, PASS, RESPONSE, DEFAULT_HOST)
