import asyncio
from echo_bot import EchoBot
import logging
import getpass


def _main(account):

    account.connect()
    account.process()

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
if opt == 1:
    try:
        xmpp = EchoBot(jid, password)
        asyncio.run(_main(xmpp))

    except KeyboardInterrupt:
        print("Bye")
#handling registration
elif opt == 2:
    try:
        xmpp = EchoBot(jid, password, is_new=True)
        asyncio.run(_main(xmpp))
    except KeyboardInterrupt:
        print("Bye")

else:
    print("Chao!")
