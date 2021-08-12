import asyncio
import logging
from aioconsole import aprint

import slixmpp
from slixmpp.exceptions import IqError, IqTimeout
import xml.etree.ElementTree as ET
class Client(slixmpp.ClientXMPP):
    def __init__(self, jid, password, is_new=False, is_removing=False):
        super().__init__(jid, password)

        self.removing = is_removing
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
        self.add_event_handler('si_request', self.request_transfer)


        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0045') # Multi-User Chat
        self.register_plugin('xep_0004') # Data Forms
        self.register_plugin('xep_0060') # PubSub
        self.register_plugin('xep_0199') # Ping
        self.register_plugin('xep_0085') # For chat state
        self.register_plugin('xep_0066')
        self.register_plugin('xep_0071')
        self.register_plugin('xep_0128')
        self.register_plugin('xep_0363')
        self.register_plugin('xep_0054') # for vmCard (profile)
        self.register_plugin('xep_0082') # for vmCard (profile)

        if is_removing:
            self.register_plugin('xep_0077') # In-band Registration        

        if is_new:
            self.register_plugin('xep_0077') # In-band Registration        
            self.register_plugin('xep_0004') # Data forms
            self.register_plugin('xep_0066') # Out-of-band Data
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
        if not self.removing:
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
        if self.removing:
            resp = self.Iq()
            resp['type'] = 'set'
            resp['username'] = self.boundjid.user
            resp['password'] = self.password
            resp['register']['remove'] = 'remove'   
            try:
                await resp.send()
                logging.info("Account removed for jid %s!" % self.boundjid)
            except IqError as e:
                logging.error("Could not remove account: %s" %
                        e.iq['error']['text'])
                self.disconnect()
            except IqTimeout:
                logging.error("No response from server.")
                self.disconnect()
            finally:
                self.disconnect()
        else:
            try:
                self.send_presence() #<presence />
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
        if self.im != None or self.room != None:
            await aprint("Writing ...")

    async def is_paused(self, event):
        if self.im != None or self.room != None:
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
        self.file = filename
    
    async def send_file(self, to):
        try:
            url = await self.plugin['xep_0363'].upload_file(
                self.file,
                domain='alumchat.xyz',
                timeout=10
            )
         
        except (IqError, IqTimeout):
            await aprint('File transfer failed')
        html = (
            f'<body xmlns="http://www.w3.org/1999/xhtml">'
            f'<a href="{url}">{url}</a></body>'
        )
        message = self.make_message(mto=to, mbody=url, mhtml=html)
        message['oob']['url'] = url
        message.send()

    async def request_transfer(self, event):
        resp = self.make_iq_result(
            id=event['id'],
            ito=event['from'],
            ifrom=self.boundjid
        )
        try:
            await resp.send()
        except (IqError, IqTimeout):
            await aprint("Error")
        

    async def view_profile(self, jid):
        # query = self.make_iq_get(
        #     ito=jid,
        #     ifrom=self.boundjid
        # )
        # query['vcard_temp']
        # try:
        #     query.send()
        # except (IqError, IqTimeout):
        #     await aprint('Error')
        
        self.plugin['xep_0054'].get_vcard(
            jid,
            self.boundjid,
            callback=self.recieve_profile,
            timeout_callback=10,
            timeout=15,
        )
    
    def recieve_profile(self, event):
        print('*'*20)
        print("jid:{}\nname:{}".format(
            event['from'],
            event['vcard_temp']['FN']))
        print('*'*20)
