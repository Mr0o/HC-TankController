import telnetlib
from time import sleep

CONTROL_PORT = 8150
DEFAULT_IP = '10.10.1.1'

try:
    tn = telnetlib.Telnet(DEFAULT_IP, CONTROL_PORT)
except:
    print("Unable to connect to ", DEFAULT_IP)
    
tn.write(b"t1\n")

while(tn):
    com = input("Type command")
    if com == "w":
        tn.write(b"1121\n")
    if com == "s":
        tn.write(b"1222\n")
    if com == "a":
        tn.write(b"1221\n")
    if com == "d":
        tn.write(b"1122\n")
    if com == "q":
        tn.write(b"31\n")
    if com == "e":
        tn.write(b"32\n")
    if com == "":
        tn.write(b"102030\n")
    
