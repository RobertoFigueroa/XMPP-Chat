import asyncio
import weakref
from echo_bot import EchoBot
import logging
import getpass
import threading
import sys
from multiprocessing import Process

from concurrent.futures import ThreadPoolExecutor

import aioconsole

async def ainput(prompt: str = ''):
    with ThreadPoolExecutor(1, 'ainput') as executor:
        return (await asyncio.get_event_loop().run_in_executor(executor, input, prompt)).rstrip()

async def  _main(account):
    account.connect()
    account.process()

def write():
    while True:
        msg = input("->")



async def ui(xmpp):

    print("1.Sesion 1a1\n2.Salir")
    opt = int(input("->"))

    if opt == 1:
        name = input("Write JID\n-> ")
        print("este es el jid", xmpp.boundjid)
        xmpp.set_im(name)
        is_session_active = True
        while is_session_active:
            msg = input("-->")
            #if msg != '\q' and len(msg)>0:
            await xmpp.send_message(name, msg, mtype='chat').send()
            if msg == '\q':
                is_session_active = False
            
    elif opt == 2:
        xmpp.log_out()
    else:
        print("Bye")


print("*"*20)
print("Welcome to Network-Chat-UVG")
print("*"*20)
print("Authentication")
print("-"*20)
print("1.Log in\n2.Create account\nAny for exit")
opt = int(input("Choose an option\n>>>"))
if opt < 3 and opt > 0:
    jid = input("Enter username: ")
    password = getpass.getpass("Password: ")
    jid += '@alumchat.xyz'
logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)-8s %(message)s')
#handling authentication
xmpp = None
if opt == 1:
    try:
        xmpp = EchoBot(jid, password)
        xmpp.connect()
        t = threading.Thread(target=ui, args=(xmpp, ))
        t.start()
        t2 = threading.Thread(target=xmpp.process)
        t2.start()
        #xmpp.process()


    except KeyboardInterrupt:
        print("Bye")
#handling registration
elif opt == 2:
    try:
        xmpp = EchoBot(jid, password, is_new=True)
        _main(xmpp)
    except KeyboardInterrupt:
        print("Bye")

else:
    print("Chao!")
    exit(0)
