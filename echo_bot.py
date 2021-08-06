import sys
import asyncio
import logging
import getpass
from optparse import OptionParser

import slixmpp

class EchoBot(slixmpp.ClientXMPP):
    def __init__(self, jid, password):
        super().__init__(jid, password)

        self.add_event_handler('session_start', self.start)
        self.add_event_handler('message', self.message)


    # if xmpp.connect():
    #     xmpp.process(block=True)
    # else:
    #     print('Unable to connect')
    #method for broadcast presence and retrieve roster when start session
    async def start(self, event):
        try:
            self.send_presence(pstatus="Prueba el ecoooo") #<presence />
            await self.get_roster() #IQ stanza for retrieve, response is saved by internal handler (self.roster)
        except:
            print("An error has ocurred")

    def message(self, msg):
        if msg['type'] in ('normal', 'chat'):
            msg.reply("Enviaste:\n%s" % msg['body']).send()
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
    # ***

    xmpp = EchoBot(opts.jid, opts.password)
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0199') # Ping

    xmpp.connect()
    xmpp.process()