import asyncio

from slixmpp.exceptions import XMPPError
from echo_bot import EchoBot
import logging
import getpass

from concurrent.futures import ThreadPoolExecutor


async def ainput(prompt: str = ''):
    with ThreadPoolExecutor(1, 'ainput') as executor:
        return (await asyncio.get_event_loop().run_in_executor(executor, input, prompt)).rstrip()

def _main(a):
    a.connect()
    a.process(forever=False)

async def main():

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
        xmpp = EchoBot(jid, password)
        await asyncio.gather(
            _main(xmpp),
            ainput()
        )

    else:
        exit(0)

asyncio.run(main())