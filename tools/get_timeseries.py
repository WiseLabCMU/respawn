#!/usr/bin/env python

# RESPAWN TIME-SERIES QUERY TOOL
# Grabs range of data from respawn datastore
# and prints out in CSV format.
# author: Max Buevich


import sys
import logging
import getpass
from optparse import OptionParser

import sleekxmpp
from sleekxmpp.xmlstream import ET, tostring
from sleekxmpp.xmlstream.matcher import StanzaPath
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.plugins.xep_0004.stanza.form import Form

import sys
import copy
import urllib2
import json
import math
import time

# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input

#--------------------------------------------


#domain = 'http://sensor.andrew.cmu.edu:4720'

def get_timeseries(domain, dev, chan, period, startt, endt):

   
   chan = chan.replace(" ","-")
   if(chan == None):
      s = urllib2.urlopen(domain+'/info.json').read()
      info = json.loads(s)
      for dc in info['channel_specs']:
         if(dev == dc.split('.')[0]):
            print dc.split('.')[1]
            for e in info['channel_specs'][dc]['channel_bounds']:
               print '\t'+e, info['channel_specs'][dc]['channel_bounds'][e]
      sys.exit(0)
   
   devchan = dev + '.' + chan
   if(period == -1):
      period = 1024
   if((startt == -1) and (endt == -1)):
      s = urllib2.urlopen(domain+'/info.json').read()
      info = json.loads(s)
      print info
      startt = info['channel_specs'][devchan]['channel_bounds']['min_time']
      endt = info['channel_specs'][devchan]['channel_bounds']['max_time']

   # round down to power of 2
   logperiod = int(math.log(period,2))
   period = math.pow(2,logperiod)
	
   tiles = int((endt-startt)/512/period)
   # RESTRICTION: error if more than 2000 tiles requested
   # RESTRICTION COMMENTED OUT
   #if(tiles > 2000):
   #	print '...'
   #	print 'error: A query with start-time', startt, 'and end-time', endt, 'and downsample period', period, ' seconds retrieves', tiles, 'tiles. 2000 tiles per query is the limit.'
   #	print '...'
   #	sys.exit(0)

   # print meta information
   print '# node:  ', dev
   print '# transducer:  ', chan
   print '# period:  ', period, 'seconds'
   print '# start t: ', startt
   print '# end t:   ', endt
   print '# tiles:   ', tiles, ('('+str(512*tiles)+' points maximum capacity)')
  
   sys.stderr.write(str(time.time())+' started: '+devchan+'\n')
   print '#'
   print '# time, value, standard deviation, count'
   # get tiles one by one and print them out
   for i in range(tiles):
      if((startt+(i*512*period))<endt):
         level = int(math.log(period,2))
         offset = int(startt/512/period) + i
         datastr = urllib2.urlopen(domain+'/tiles/1/'+devchan+'/'+str(level)+'.'+str(offset)+'.json').read(); #time.sleep(0.1);
         data = json.loads(datastr)
         if(data['data'] == []):
            #sys.stderr.write('# empty tile!\n')
            continue
         for el in data['data']:
            if(el[1] != -1e+308): 
               for subel in el:
                  print str(subel) + ',',
               print ''

   sys.stderr.write(str(time.time())+' finished: '+devchan+'\n')


class PubsubEvents(sleekxmpp.ClientXMPP):

    def __init__(self, jid, password,
                        dev, chan, period, startt, endt, pubsub=''):
        super(PubsubEvents, self).__init__(jid, password)

        self.register_plugin('xep_0030')
        self.register_plugin('xep_0059')
        self.register_plugin('xep_0060')

        self.pubsub = pubsub
        self.dev = dev
        self.chan = chan
        self.startt = startt
        self.endt = endt
        self.period = period

        self.add_event_handler('session_start', self.start)

    def start(self, event):
        self.get_roster()
        self.send_presence()

        node = self.dev
        d = self['xep_0060'].get_item(self.pubsub, node, 'storage')
        #print d
        if(d['pubsub']['items']['item']['payload']):
            for a in d['pubsub']['items']['item']['payload']:
               if(a.tag.split('}',1)[-1] == 'address'):
                  #print a.attrib['link']
                  domain = a.attrib['link']
        
        get_timeseries(domain, self.dev, self.chan, self.period, self.startt, self.endt)
        sys.exit(0)


def main():

    # Setup the command line arguments.
    optp = OptionParser()
    optp.usage = "%prog -j jid@host -p passwd NODE [TRANSDUCER] [RES_PERIOD] [START_TIME] [END_TIME]"

    # Output verbosity options.
    #optp.add_option('-q', '--quiet', help='set logging to ERROR',
    #                action='store_const', dest='loglevel',
    #                const=logging.ERROR, default=logging.INFO)
    #optp.add_option('-d', '--debug', help='set logging to DEBUG',
    #                action='store_const', dest='loglevel',
    #                const=logging.DEBUG, default=logging.INFO)
    #optp.add_option('-v', '--verbose', help='set logging to COMM',
    #                action='store_const', dest='loglevel',
    #                const=5, default=logging.INFO)

    # JID and password options.
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")

    opts, args = optp.parse_args()

    # Setup logging.
    #logging.basicConfig(level=opts.loglevel,
    #                    format='%(levelname)-8s %(message)s')
    logging.basicConfig(level=logging.ERROR,
                        format='%(levelname)-8s %(message)s')

    if opts.jid is None:
        #opts.jid = 'user@server.org'
        optp.print_help()
        exit()
    if opts.password is None:
        #opts.password = 'password'
        optp.print_help()
        exit()
    if(len(args) == 1):
        args.append(None)
        args.append(-1)
        args.append(-1)
        args.append(-1)
    if(len(args) == 2):
        args.append(-1)
        args.append(-1)
        args.append(-1)
    if(len(args) == 3):
        args.append(-1)
        args.append(-1)
    if(len(args) != 5):
        optp.print_help()
        exit()

    pubsub = 'pubsub.'+opts.jid.split('@')[1]
    # Setup the PubsubEvents listener
    xmpp = PubsubEvents(opts.jid, opts.password,
         args[0], args[1], float(args[2]), float(args[3]), float(args[4]), pubsub=pubsub)

    # If you are working with an OpenFire server, you may need
    # to adjust the SSL version used:
    # xmpp.ssl_version = ssl.PROTOCOL_SSLv3

    # If you want to verify the SSL certificates offered by a server:
    # xmpp.ca_certs = "path/to/ca/cert"

    # Connect to the XMPP server and start processing XMPP stanzas.
    if xmpp.connect():
        # If you do not have the dnspython library installed, you will need
        # to manually specify the name of the server if it does not match
        # the one in the JID. For example, to use Google Talk you would
        # need to use:
        #
        # if xmpp.connect(('talk.google.com', 5222)):
        #     ...
        xmpp.process(block=True)
        #print("Done")
    else:
        print("Unable to connect.")


if __name__ == '__main__':
   main()
