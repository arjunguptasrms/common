import pexpect
import subprocess
import re
import threading
import time
import datetime

def runLinuxCmd(cmd):
    p = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=True)
    op,err = p.communicate()
    return op.decode('utf-8').strip()


def getTimeofSipMsg(fileName,message,direction):
    fl = open(fileName,"r")
    sipMsgFound = 0
    sipMesg = ""
    pt1 = "^----"
    timestamp = ""
    found_direction = ""
    for line in fl:
        
        if found_direction == 1 and sipMsgFound == 1:
            sipMesg += line
        if sipMsgFound == 1:
            if "UDP message received" in line:
                message_direction = "incoming"
                if message_direction == direction:
                    found_direction = 1
            if "UDP message sent" in line:
                message_direction = "outgoing"
                if message_direction == direction:
                    found_direction = 1
            
        if "-----------------------" in line:
            sipMsgFound = 1
            desire_mesg = 0
            if len(sipMesg) > 1:
                for header in message:
                    if header in sipMesg:
                        desire_mesg = 1
                    else:
                        desire_mesg = 0
                if desire_mesg == 1:
                    return timestamp
            sipMesg = ""
            
            timestamp = " ".join(line.split()[1:])


runLinuxCmd("rm -f *.log")
##
time.sleep(2)
runLinuxCmd("sipp -sf UE1.xml -m 1 -i 10.0.2.15 -p 5060 52.9.254.123:5060 -trace_msg -bg")
time.sleep(2)
runLinuxCmd("sipp -sf UE2.xml -m 1 -i 10.0.2.15 -p 5070 52.9.254.123:5060 -trace_msg -bg")
time.sleep(2)
runLinuxCmd("sipp -sf UAS.xml -m 1 -i 10.0.2.15 -p 5070 -mi 10.0.2.15 -mp 5072 -rtp_echo 52.9.254.123:5060 -trace_msg -bg")
time.sleep(2)
runLinuxCmd("sipp -sf UAC.xml -m 1 -i 10.0.2.15 -p 5060 -mi 10.0.2.15 -mp 5062 -rtp_echo 52.9.254.123:5060 -trace_msg -bg")
time.sleep(60)


uas_file = runLinuxCmd("ls UAS_*")
uac_file = runLinuxCmd("ls UAC_*")

t1 = getTimeofSipMsg(uas_file,["INVITE sip:test895187951711567647677"],"incoming")
print(t1)
t2 = getTimeofSipMsg(uac_file,["SIP/2.0 200 OK","CSeq: 2 INVITE"],"incoming")

print(t2)


t3 = getTimeofSipMsg(uas_file,["BYE sip:Plivo"],"outgoing")
print(t3)

#2021-12-05 15:30:29.698253
#pattern = '%Y-%m-%d %H:%M:%S.%f'

Bye_time = datetime.datetime.fromisoformat(t3).strftime('%s')
ans_time = datetime.datetime.fromisoformat(t2).strftime('%s')

delta = int(Bye_time) - int(ans_time)
print("call duration",delta)
