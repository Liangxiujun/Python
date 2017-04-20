#!/usr/bin/python
#--*--coding:utf8--*--
import multiprocessing
import re
import os
import sys
import commands
import datetime


def pinger(count,ip):

  cmd = 'ping -c %d  %s' %(int(count),ip.strip())
  ret = commands.getoutput(cmd)
  loss_re = re.compile(r"received,(.*) packet loss,")
  packet_loss = loss_re.findall(ret)[0]
  rtt_re = re.compile(r"rtt min/avg/max/mdev = (.*) ")
  rtts = rtt_re.findall(ret)
  try:
    rtt = rtts[0].split('/')

    rtt_min = rtt[0]
    rtt_avg = rtt[1]
    rtt_max = rtt[2]
    print "%s\t%s\t%s\t%s\t%s" %(ip,packet_loss,rtt_min,rtt_avg,rtt_max)
  except Exception,e:
    print "%s\t%s\t%s\t%s\t%s" %(ip,None,None,None,None)


if __name__ == '__main__':
  if not os.path.exists('./server.list'):
    print '\033[31m Error: server.list 不存在，请重试\033[0m'
    sys.exit(1)
  now = datetime.datetime.now()
  ip_list = open('server.list','r').readlines()
  pool = multiprocessing.Pool(processes=4)
  result = []
  print "########%s##########"%now
  print "ip\t\tpacket\trtt_min\trtt_avg\trtt_max"
  for ip in ip_list:
    ip = ip.strip()
    if len(ip) == 1 or ip.startswith("#"):
      continue
    result.append(pool.apply_async(pinger,(2,ip,)))
  pool.close()
  pool.join()
