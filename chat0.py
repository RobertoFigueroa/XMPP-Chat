import asyncio
import logging
import getpass

from slixmpp import clientxmpp

from echo_bot import EchoBot
from aioconsole import ainput


async def main(client : EchoBot):
    print("-"*20)
    print("1.Chat 1-2-1\n2.Other stuff\nAny number for exit")
    opt = int(input("Choose an option\n->"))
    if opt == 1:
        name = await ainput("Write JID\n-> ")
        client.set_im(name)
        is_session_active = True
        while is_session_active:
            msg = await ainput("-->")
            if msg != '\q' and len(msg)>0:
                client.send_message(
                    mto=name,
                    mbody=msg,
                    mtype='chat'
                )
            else:
                is_session_active = False

if __name__ == "__main__":
    try:
        #TODO: manage input for registration or authentication
        client = EchoBot("reg1@alumchat.xyz", "12345")
        client.connect()
        client.loop.run_until_complete(client.connected_event.wait())
        print("Conectando ....")
        client.loop.create_task(main(client))
        client.process()
        #loop = asyncio.get_running_loop()
    except Exception as e:
        print("Error:", e)
    finally:
        client.disconnect()
