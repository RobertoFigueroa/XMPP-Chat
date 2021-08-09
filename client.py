import sys
import asyncio
import logging
import getpass
from optparse import OptionParser
import threading
from aioconsole import aprint

import slixmpp
from slixmpp.exceptions import IqError, IqTimeout

class Client(slixmpp.ClientXMPP):
    def __init__(self, jid, password, is_new=False):
        super().__init__(jid, password)

        self.im = None

        self.connected_event = asyncio.Event()
        
        self.add_event_handler('session_start', self.start)
        self.add_event_handler('message', self.message)
        self.add_event_handler('register', self.register)
        
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0004') # Data Forms
        self.register_plugin('xep_0060') # PubSub
        self.register_plugin('xep_0199') # Ping
        if is_new:
            self.register_plugin('xep_0004') # Data forms
            self.register_plugin('xep_0066') # Out-of-band Data
            self.register_plugin('xep_0077') # In-band Registration        
            self['xep_0077'].force_registration = True

    async def chat_to(self, to, msg):
        self.send_message(mto=to, mbody=msg, mtype='chat', mfrom=self.boundjid)
        await asyncio.sleep(1)
    def log_out(self):
        self.disconnect(reason='Log out')

    def set_im(self, jid):
        self.im = jid
    
    def clear_im(self, jid):
        self.im = None

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
            self.send_presence(pstatus="Prueba el ecoooo") #<presence />
            await self.get_roster() #IQ stanza for retrieve, response is saved by internal handler (self.roster)
            self.connected_event.set()
        except:
            print("An error has ocurred")

    async def message(self, msg):
        if msg['type'] in ('normal', 'chat'):
            #if msg['from'] == self.im:
            await aprint("\n{}".format(msg['body']))
            #msg.reply("Enviaste:\n%s" % msg['body']).send()
            #algo we can use send_message
            #self.send_message(mto=msg['from'],
            #                        mbody="Thanks for sending:\n%s" % msg['body'])


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
    xmpp = EchoBot(opts.jid, opts.password)
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0199') # Ping

    xmpp.connect()
    xmpp.process()