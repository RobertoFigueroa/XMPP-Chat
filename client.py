#libraries
import asyncio
import logging
from aioconsole import aprint

import slixmpp
from slixmpp.exceptions import IqError, IqTimeout
import xml.etree.ElementTree as ET


class Client(slixmpp.ClientXMPP):

    """
    Class for manage client conection and functionalities
    -------------------------------------------------------------------
    PARAMETERS: 
    jid : str
        JID of user
    password : str
        user password
    is_new : boolean, optional
        indicates if user is registering or authenticating
    is_removing : boolean, optional
        indicates if removing account
    """
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
        
        # Event for maganage conection
        self.connected_event = asyncio.Event()
        self.presences_received = asyncio.Event()

        #handlers for manage triggers
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

        #necessary plugins
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0045') # Multi-User Chat
        self.register_plugin('xep_0004') # Data Forms
        self.register_plugin('xep_0060') # PubSub
        self.register_plugin('xep_0199') # Ping
        self.register_plugin('xep_0085') # For chat state
        self.register_plugin('xep_0066') # Plugin dependencies:
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

    """
    Set the receiver for instant messages
    jid : str
        JID of receiver
    """
    def set_im(self, jid):
        self.im = jid
    

    """
    Clears the receiver for instant messages
    """
    def clear_im(self):
        self.im = None

    """
    Corrutine for get roster
    """
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

    """
    Corrutine for adding a new contact
    cjid : str
        JID of user the be add
    """
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

    """
    Corrutine for register a new user 
    """        
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

    """
    Corrutine for manage start session
    """
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

    """
    corrutine for recieve messages
    """
    async def message(self, msg):
        if msg['type'] in ('normal', 'chat'):
            await aprint("\n{}".format(msg['body']))

    """
    Function to track how many roster entries have received presence updates. 
    """
    def wait_for_presences(self, pres):
            self.received.add(pres['from'].bare)
            if len(self.received) >= len(self.client_roster.keys()):
                self.presences_received.set()
            else:
                self.presences_received.clear()

    """
    Process incoming message stanzas from a chat room
    """
    async def muc_message(self, msg):
        if msg['mucnick'] != self.nick:
            if msg['type'] in ('groupchat', ):
                await aprint("\n{}".format(msg['body']))

    """
    Process a presence stanza from a chat room
    """
    def muc_online(self, presence):
        
        if presence['muc']['nick'] != self.nick:
            pass
            # self.send_message(mto=presence['from'].bare,
            #                   mbody="Hello, %s %s" % (presence['muc']['role'],
            #                                           presence['muc']['nick']),
            #                   mtype='groupchat')

    """
    Join to a MUC room
    """
    def join_room(self):
        self.plugin['xep_0045'].join_muc(self.room,
                                         self.nick)

    """
    Process composing notification
    """
    async def is_composing(self, event):
        if self.im != None or self.room != None:
            await aprint("Writing ...")

    """
    Process paused notification
    """
    async def is_paused(self, event):
        if self.im != None or self.room != None:
            await aprint("Stop writing")
    """
    Process gone notification
    """
    async def is_gone(self, event):
        await aprint("Gone ... ")

    """
    Send chat status to a IM user
    """
    def notify_status(self, mto, status):
        status_msg = self.make_message(
            mto=mto,
            mfrom=self.boundjid,
            mtype='chat'
        )

        status_msg['chat_state'] = status
        status_msg.send()

    
    """
    Function for set filename var
    """
    def open_file(self, filename):
        self.file = filename
    
    """
    Corrutine for send a file to a user
    """
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

    """
    Corrutine for request transfer file 
    """    
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
        
    """
    Corrutine for view profile
    """
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
    
    """
    Manage recieve vcard stanza (for profile)
    """
    def recieve_profile(self, event):
        print('*'*20)
        print("jid:{}\nname:{}".format(
            event['from'],
            event['vcard_temp']['FN']))
        print('*'*20)
