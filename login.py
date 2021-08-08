import sys
import asyncio
import logging
import getpass
from optparse import OptionParser

import slixmpp


class Login(slixmpp.ClientXMPP):

    def __init__(self, jid, password):
        super().__init__(jid, password)

        self.add_event_handler("session_start", self.start)

        self.add_event_handler("register", self.register)

    async def start(self, event):

        self.send_presence()
        await self.get_roster()

    
    async def register(self, iq):

        resp = self.Iq()