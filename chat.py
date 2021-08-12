import logging
import getpass
from aioconsole.stream import aprint
from optparse import OptionParser

from client import Client
from aioconsole import ainput

async def main(client : Client):
    global msg
    is_connected = True
    while is_connected:
        print("-"*20) 
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
                if (msg != '\q' and msg != 'file:') and len(msg)>0:
                    client.send_message(
                        mto=name,
                        mbody=msg,
                        mtype='chat' 
                    )
                elif len(msg) == 0:
                    client.notify_status(name, 'paused')
                    
                elif msg == '\q':
                    client.im = None
                    is_session_active = False
                elif msg == 'file:':
                    file_dir = await ainput("Write file directory\n-->")
                    await aprint("Sending file ...")
                    client.open_file(file_dir)
                    await client.send_file(name)
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
            jid = await ainput("Type JID:\n-->")
            await client.view_profile(jid)
        elif opt == 5:
            room = await ainput("Write room name\n-->")
            client.room = room
            client.join_room()
            room_session = True
            while room_session:
                msg = await ainput("-->")
                if msg != '\q' and msg != 'file:' and len(msg) > 0:
                    client.send_message(
                        mto=client.room,
                        mbody=msg,
                        mtype='groupchat',
                        mfrom=client.boundjid
                    )
                elif msg == '\q':
                    client.room = None
                    room_session = False
                elif msg == 'file:':
                    file_dir = await ainput("Write file directory\n-->")
                    await aprint("Sending file ...")
                    client.open_file(file_dir)
                    await client.send_file(client.room)
                else:
                    pass
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

    optp = OptionParser()

    optp.add_option('-d', '--debug', help='set loggin to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")
    optp.add_option("-n", "--new", dest="is_new",
                    help="is registering a new user", 
                    action='store_const',
                    const=True, default=False)
    optp.add_option("-r", "--remove", dest="is_removing",
                    help="remove given jid", action="store_const",
                    const=True, default=False)

    opts, args = optp.parse_args()

    if opts.jid is None:
        opts.jid = input("Username (JID): ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")  

    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    try:
        client = Client(opts.jid, opts.password, opts.is_new, opts.is_removing)
        if opts.is_new:
            print("Registrando ...")
        if opts.is_removing:
            print("Requesting remove JID...")
        print("Conectando ....")
        client.connect() 
        client.loop.run_until_complete(client.connected_event.wait())
        client.loop.create_task(main(client))
        client.process(forever=False)
    except Exception as e:
        print("Error:", e)
    finally:
        client.disconnect()
