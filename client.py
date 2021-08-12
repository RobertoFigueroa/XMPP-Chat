from os import EX_PROTOCOL, sendfile
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
        self.nick = jid.split('@')[0]
        self.room = None
        self.last_msg = None
        self.file = None
        self.receiver = None
        
        self.received = set()
        
        self.connected_event = asyncio.Event()
        self.presences_received = asyncio.Event()

        self.add_event_handler('session_start', self.start)
        self.add_event_handler('message', self.message)
        self.add_event_handler('register', self.register)
        self.add_event_handler('changed_status', self.wait_for_presences)
        self.add_event_handler("groupchat_message", self.muc_message)
        self.add_event_handler("muc::%s::got_online" % self.room,
                               self.muc_online)
        self.add_event_handler('chatstate_composing', self.is_composing)
        self.add_event_handler('chatstate_paused', self.is_paused)
        self.add_event_handler('chatstate_gone', self.is_gone)


        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0045') # Multi-User Chat
        self.register_plugin('xep_0004') # Data Forms
        self.register_plugin('xep_0060') # PubSub
        self.register_plugin('xep_0199') # Ping
        self.register_plugin('xep_0085') # For chat state
        self.register_plugin('xep_0065') # SOCKS5 Bytestreams
        #self.register_plugin('xep_0095') # SOCKS5 Bytestreams
        #self.register_plugin('xep_0096') # SOCKS5 Bytestreams
        #self.register_plugin('xep_0047') # In-band send file

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

    async def muc_message(self, msg):
        """
        Process incoming message stanzas from any chat room. Be aware
        that if you also have any handlers for the 'message' event,
        message stanzas may be processed by both handlers, so check
        the 'type' attribute when using a 'message' event handler.
        Whenever the bot's nickname is mentioned, respond to
        the message.
        IMPORTANT: Always check that a message is not from yourself,
                   otherwise you will create an infinite loop responding
                   to your own messages.
        This handler will reply to messages that mention
        the bot's nickname.
        Arguments:
            msg -- The received message stanza. See the documentation
                   for stanza objects and the Message stanza to see
                   how it may be used.
        """
        if msg['mucnick'] != self.nick:
            if msg['type'] in ('groupchat', ):
                await aprint("\n{}".format(msg['body']))

    def muc_online(self, presence):
        """
        Process a presence stanza from a chat room. In this case,
        presences from users that have just come online are
        handled by sending a welcome message that includes
        the user's nickname and role in the room.
        Arguments:
            presence -- The received presence stanza. See the
                        documentation for the Presence stanza
                        to see how else it may be used.
        """
        if presence['muc']['nick'] != self.nick:
            pass
            # self.send_message(mto=presence['from'].bare,
            #                   mbody="Hello, %s %s" % (presence['muc']['role'],
            #                                           presence['muc']['nick']),
            #                   mtype='groupchat')

    def join_room(self):
        self.plugin['xep_0045'].join_muc(self.room,
                                         self.nick)

    async def is_composing(self, event):
        await aprint("Writing ...")

    async def is_paused(self, event):
        await aprint("Stop writing")
    
    async def is_gone(self, event):
        await aprint("Gone ... ")

    def notify_status(self, mto, status):
        status_msg = self.make_message(
            mto=mto,
            mfrom=self.boundjid,
            mtype='chat'
        )

        status_msg['chat_state'] = status
        status_msg.send()

    def open_file(self, filename):
        self.file = open(filename, 'rb')
    
    async def send_file(self, to):
        proxy = await self['xep_0065'].handshake(to, self.boundjid)
        try:
            while True:
                data = self.file.read(1048576)
                if not data:
                    break
                await proxy.write(data)
            proxy.transport.write_eof()
        except (IqError, IqTimeout):
            await aprint('File transfer failed')
        else:
            await aprint('File transfer success')
        finally:
            self.file.close()

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