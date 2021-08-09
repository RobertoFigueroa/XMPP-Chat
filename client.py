from os import EX_PROTOCOL
import sys
import asyncio
import logging
import getpass
from optparse import OptionParser
import threading
from aioconsole import aprint

import slixmpp
from slixmpp.exceptions import IqError, IqTimeout
import xml.etree.ElementTree as ET

class Client(slixmpp.ClientXMPP):
    def __init__(self, jid, password, is_new=False):
        super().__init__(jid, password)

        self.im = None
        
        self.recieved = set()
        
        self.connected_event = asyncio.Event()
        self.presences_received = asyncio.Event()

        self.add_event_handler('session_start', self.start)
        self.add_event_handler('message', self.message)
        self.add_event_handler('register', self.register)
        self.add_event_handler("changed_status", self.wait_for_presences)
        
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0004') # Data Forms
        self.register_plugin('xep_0060') # PubSub
        self.register_plugin('xep_0199') # Ping

        if is_new:
            self.register_plugin('xep_0004') # Data forms
            self.register_plugin('xep_0066') # Out-of-band Data
            self.register_plugin('xep_0077') # In-band Registration        
            self['xep_0077'].force_registration = True

    def set_im(self, jid):
        self.im = jid
    
    def clear_im(self, jid):
        self.im = None

    async def my_roster(self):
        print("Waiting for presence updates ...\n")
        await asyncio.sleep(10)

        print('Roster for %s' % self.boundjid.bare)
        groups = self.client_roster.groups()
        for group in groups:
            print('\n%s' % group)
            print('-' * 72)
            for jid in groups[group]:
                sub = self.client_roster[jid]['subscription']
                name = self.client_roster[jid]['name']
                if self.client_roster[jid]['name']:
                    print(' %s (%s) [%s]' % (name, jid, sub))
                else:
                    print(' %s [%s]' % (jid, sub))

                connections = self.client_roster.presence(jid)
                for res, pres in connections.items():
                    show = 'available'
                    if pres['show']:
                        show = pres['show']
                    print('   - %s (%s)' % (res, show))
                    if pres['status']:
                        print('       %s' % pres['status'])

    async def add_contact(self, cjid):
        resp =self.Iq()
        resp['from'] = self.boundjid
        resp['type'] = 'set'
        resp['query'] = 'jabber:iq:roster'
        payload = ET.fromstring("<query xmlns='jabber:iq:roster'><item jid='%s'><group>Friends</group></item></query>" % cjid)
        resp.set_payload(payload)
        try:
            await resp.send()
        except IqError as e:
            logging.error("Could not add account: %s" 
                    % e.iq['error']['text'])
            aprint("Could not add account")
        except IqTimeout:
            logging.error("No response from server.")
            aprint("Timeout, no response from server")
        except:
            print("Error while adding account")
        #resp = self.Iq()
        # resp['from'] = self.boundjid
        # resp['type'] = 'set'
        # resp['query']['xmlns'] = 'jabber:iq:roster'
        # resp['query'][''] 
        

    async def register(self, iq):
        resp = self.Iq()
        resp['type'] = 'set'
        resp['register']['username'] = self.boundjid.user
        resp['register']['password'] = self.password

        try:
            await resp.send()
            logging.info("Account created for %s!" % self.boundjid)
        except IqError as e:
            logging.error("Could not register account: %s" %
                    e.iq['error']['text'])
            self.disconnect()
        except IqTimeout:
            logging.error("No response from server.")
            self.disconnect()

        
    # if xmpp.connect():
    #     xmpp.process(block=True)
    # else:
    #     print('Unable to connect')
    #method for broadcast presence and retrieve roster when start session
    async def start(self, event):
        try:
            self.send_presence(pstatus="hola khe aze") #<presence />
            await self.get_roster() #IQ stanza for retrieve, response is saved by internal handler (self.roster)
            self.connected_event.set()
        except IqError as err:
            print('Error: %s' % err.iq['error']['condition'])
        except IqTimeout:
            print('Error: Request timed out')

    async def message(self, msg):
        if msg['type'] in ('normal', 'chat'):
            #if msg['from'] == self.im:
            await aprint("\n{}".format(msg['body']))
            #msg.reply("Enviaste:\n%s" % msg['body']).send()
            #algo we can use send_message
            #self.send_message(mto=msg['from'],
            #                        mbody="Thanks for sending:\n%s" % msg['body'])

    def wait_for_presences(self, pres):
            """
            Track how many roster entries have received presence updates.
            """
            self.received.add(pres['from'].bare)
            if len(self.received) >= len(self.client_roster.keys()):
                self.presences_received.set()
            else:
                self.presences_received.clear()

if __name__ == "__main__":
    optp = OptionParser()

    optp.add_option('-d', '--debug', help='set loggin to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")

    opts, args = optp.parse_args()

    if opts.jid is None:
        opts.jid = input("Username: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")
    

    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')



    # ***
    # service discovery and ping
    # ***z
    xmpp = Client(opts.jid, opts.password)
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0199') # Ping

    xmpp.connect()
    xmpp.process()