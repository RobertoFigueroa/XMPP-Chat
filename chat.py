import asyncio
import logging
import getpass
import time
from aioconsole.stream import aprint

from slixmpp import clientxmpp

from client import Client
from aioconsole import ainput
import xml.etree.ElementTree as ET

msg = ''

async def main(client : Client):
    global msg
    is_connected = True
    while is_connected:
        print("-"*20) #TODO: consider save this message on a conf. file
        print("\t\t1.Chat 1-2-1\n \
            2.Show roster\n \
            3.Add friend\n \
            4.Contact details\n \
            5.Room chat\n \
            6.Presence status\n \
            7. Send file\n \
            8.Log out\n")
        opt = int( await ainput("Choose an option\n->"))
        if opt == 1:
            name = await ainput("Write JID\n-> ")
            client.set_im(name)
            is_session_active = True
            client.notify_status(name, 'active')
            while is_session_active:
                client.notify_status(name, 'composing')
                msg = await ainput("-->")
                client.notify_status(name, 'paused')
                if msg != '\q' and len(msg)>0:
                    client.send_message(
                        mto=name,
                        mbody=msg,
                        mtype='chat' 
                    )
                elif msg == '\q':
                    client.notify_status(name, 'gone')
                    is_session_active = False
                else:
                    pass
        elif opt == 2:
            await client.my_roster()
        elif opt == 3:
            fjid = await ainput("Friend's JID \n--> ")
            print("Sending request ...")
            client.send_presence_subscription(
                pto=fjid,
                pfrom=client.boundjid
            )
            print("Request sent!")
        elif opt == 4:
            pass
        elif opt == 5:
            room = await ainput("Write room name\n-->")
            client.room = room
            client.join_room()
            room_session = True
            while room_session:
                msg = await ainput("-->")
                if msg != '\q' and len(msg) > 0:
                    client.send_message(
                        mto=client.room,
                        mbody=msg,
                        mtype='groupchat',
                        mfrom=client.boundjid
                    )
                else:
                    room_session = False
        elif opt == 6:
            status = await ainput("Write your presence\n-->")
            client.send_presence(pstatus=status)
        elif opt == 7:
            jid = await ainput("Write JID\n-->")
            file_dir = await ainput("Write file directory\n-->")
            await aprint("Sending file ...")
            client.open_file(file_dir)
            await client.send_file(jid)
        elif opt == 8:
            is_connected = False
            client.disconnect(reason='Not available, bye')
        else:
            pass


if __name__ == "__main__":
    
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-8s %(message)s')

    try:
        #TODO: manage input for registration or authentication
        client = Client("reg1@alumchat.xyz", "12345")
        print("Conectando ....")
        client.connect() 
        client.loop.run_until_complete(client.connected_event.wait())
        client.loop.create_task(main(client))
        client.process(forever=False)
        #loop = asyncio.get_running_loop()
    except Exception as e:
        print("Error:", e)
    finally:
        client.disconnect()
