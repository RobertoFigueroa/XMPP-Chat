import asyncio
from echo_bot import EchoBot
import logging

def _main(account):

    account.connect()
    account.process()

print("Welcome to Chat-UVG")
print("*"*20)
print("1.Authenticate\n2.Register\n3.Salir\n")
opt = int(input(">>> "))

#handling authentication
if opt == 1:
    try:
        ac = EchoBot("reg1@alumchat.xyz", "12345")
        ac.register_plugin('xep_0030') # Service Discovery
        ac.register_plugin('xep_0004') # Data forms
        ac.register_plugin('xep_0066') # Out-of-band Data
        ac.register_plugin('xep_0077') # In-band Registration        
        asyncio.run(_main(ac))

    except KeyboardInterrupt:
        print("Adios")


#handling registration
elif opt == 2:
    pass

#exit
else: 
    pass