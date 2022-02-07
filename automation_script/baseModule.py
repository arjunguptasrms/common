#!/usr/bin/python
#author : Arjun Gupta
import pexpect
import sys
import re
import time
import os
import subprocess
from datetime import datetime
import logging
from enviorment import *
import smtplib, ssl

print automation_log
logging.basicConfig(filename=automation_log,filemode='w',level='DEBUG',format= '<%(asctime)s,%(levelname)s,%(filename)s,%(funcName)s> %(message)s')
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
logging.getLogger('').addHandler(console)


def run_remote_cmd(ip,cmds,username = "root",passw="mavenir",tmout = 200):
    logging.info("this is command >>> "+ str(cmds))
    output = ""
    try:
        ch = pexpect.spawn("ssh "+username+"@"+ip)
        i =  ch.expect(["password","#","continue connecting"],timeout=120)
        if i == 0:
            ch.sendline(passw)
            chExp = ch.expect(["#|\$"])
            if chExp == 0:
                pass
            else:
                print "username/password is not correct"
                return 0
        if i == 1:
            pass
        if i == 2:
            ch.sendline("yes")
            ch.expect("password",timeout=30)
            ch.sendline(passw)
            chExp = ch.expect(["#|\$"])
            if chExp == 0:
                pass
            else:
                print "username/password is not correct"
                return 0
    
        if type(cmds) == list:
            for cmd in cmds:
                ch.sendline(cmd)
                ch.expect("#|\$",timeout=tmout)
                output = output+ch.before
    
        elif type(cmds) == str:
            ch.sendline(cmds)
            ch.expect("#|\$",timeout=tmout)
            output = output+ch.before
    
        return output
    except (pexpect.exceptions.TIMEOUT, pexpect.exceptions.EOF):
        print("IP is not reachable")
        return 0

#def getscp_cmd(cmd,passw="mavenir",tmout = 300):
#    logging.debug("this is command >>> " +  cmd)
#    ch = pexpect.spawn(cmd)
#    ch.expect("password")
#    ch.sendline(passw)
#    ch.expect(pexpect.EOF,tmout)
#    logging.debug(ch.before)

def getscp_cmd(cmd,passw="mavenir",tmout = 600):
    print("this is command >>> " +  cmd)
    try:
        ch = pexpect.spawn(cmd)
        i = ch.expect(["password","continue connecting",pexpect.EOF],tmout)
        if i == 2:
            pass
        if i == 0:
            ch.sendline(passw)
            checkoutput = ch.expect(["password",pexpect.EOF],tmout)
            if checkoutput == 0:
                print("username password for scp is not correct")
                return 0
            if checkoutput == 1:
                pass

        if i == 1:
            ch.sendline("yes")
            ch.expect("password")
            ch.sendline(passw)
            checkoutput = ch.expect(["password",pexpect.EOF],tmout)
            if checkoutput == 0:
                print("username password for scp is not correct")
                return 0
            if checkoutput == 1:
                pass
        print(ch.before)
    except (pexpect.exceptions.TIMEOUT, pexpect.exceptions.EOF):
        print("IP is not reachable")
        return 0


def getLinuxOutput(cmd):   
    p = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=True)
    stdout,stderr= p.communicate()
    logging.info("this is return code" + str(p.returncode))
    if p.returncode:
        logging.error("ERR :: "+cmd+ " :: is not executed successfully")
        return 0
    else:
        logging.debug("DBG :: "+cmd+ " :: executed successfully")
        return stdout.strip()



def dbChange(sqlQuery):
    if type(sqlQuery) == list:
        for cmd in sqlQuery:
            cmd = 'mysql -pmavenir mnode_cm_data -e'+' "'+cmd+'"'
            run_remote_cmd(db_ip,cmd)
    if type(sqlQuery) == str:
        sqlQuery = 'mysql -pmavenir mnode_cm_data -e'+' "'+sqlQuery+'"'
        run_remote_cmd(db_ip,sqlQuery)

def dbParameterChange(sqlQuery):
    if type(sqlQuery) == list:
	for cmd in sqlQuery:
	    cmd = 'mysql -pmavenir mnode_cm_data -e'+' "'+cmd+'"'
            result= run_remote_cmd(db_ip,cmd)
            logging.info("this is the result" + str(result))
    if type(sqlQuery) == str:
        sqlQuery = 'mysql -pmavenir mnode_cm_data -e'+' "'+sqlQuery+'"'
        result = run_remote_cmd(db_ip,sqlQuery)
        logging.info("this is the result" + str(result))


def restrtIMSservice(m_ip):
    run_remote_cmd(m_ip,"service IMS stop","root","mavenir",120)
    run_remote_cmd(m_ip,"kill -9 $(ps -ef|grep IMS |grep -v grep |awk '{print $2}')")
    time.sleep(10)
    run_remote_cmd(m_ip,"service IMS start")
    checkIMSservice(db_ip)    

def checkIMSservice(card="all"):
    fail = 1
    number_of_card = 0
    checkCount = 0
    if card == "all":
        output = run_remote_cmd(node_gm_ip,"readShm|grep 'STATE_'|awk '{print $7}'")
        for line in output.split('\n'):
            patt = re.search(r'STATE_',line)
            if patt:
                number_of_card += 1

        number_of_card = number_of_card - 1
        logging.debug("number_of_card is " + str(number_of_card))
        for i in range(30):
            output = run_remote_cmd(node_gm_ip,"readShm|grep 'STATE_'|awk '{print $7}'")
            if checkCount == number_of_card:
                logging.debug("All cards are UP")
                break

            for line in output.split('\n'):
                if line.find('readShm') == -1 and line.find('root@0-9') == -1:
                    logging.debug("line is >>>>>>>"+line)
                    line = line.strip()
                    if line != "STATE_INS_ACTIVE":
                        time.sleep(5)
                        fail = 0
                        break
                    else:
                        checkCount =+ 1
    if fail == 0:
        logging.debug("cards are not coming up")
        return 0
    else:
        return 1

def startCplane_log(ip=node_gm_ip):
    cmd = ["cd /data/storage/log","./start_up.sh"]
    run_remote_cmd(ip,cmd)


def startUplane_log():
    cmd = ["cd /data/storage/log","./start_up.sh"]
    run_remote_cmd(uplane_gm_ip,cmd)

def getCPlane_log(path = None):
    cmd = ["cd /data/storage/log","./stop_log.sh"]
    run_remote_cmd(node_gm_ip,cmd)
    if path:
        cmd = "scp root@"+node_gm_ip+":/data/storage/log/webrtc_UAGC_*log "+ path
    else:
        cmd = "scp root@"+node_gm_ip+":/data/storage/log/webrtc_UAGC_*log /root/"
    getscp_cmd(cmd)

def getCplan_logPcap(name):
    cmd = ["date '+%Y%m%d%H%M%S'"]
    output = run_remote_cmd(node_gm_ip,cmd)
    date_time_stamp = ""
    for line in output.split("\n"):
        line = line.strip()
        if line.isdigit() and len(line) == 14:
            date_time_stamp = line.strip()

    tarName = "tar -cvzf " + name + "_" + date_time_stamp +".tgz" + " webrtc_UAGC_*"
    cmd = ["cd /data/storage/log","./stop_log.sh", tarName]
    run_remote_cmd(node_gm_ip,cmd)
    if not os.path.isdir("/home/mavenir/automation_log_pcap/"):
        getLinuxOutput("mkdir -p /home/mavenir/automation_log_pcap/")
    cmd = "scp root@"+node_gm_ip+":/data/storage/log/" + name+ "_" + date_time_stamp + ".tgz"+ " /home/mavenir/automation_log_pcap/"
    getscp_cmd(cmd)


def stop_logs(name,ip=node_gm_ip):
    cmd = ["date '+%Y%m%d%H%M%S'"]
    output = run_remote_cmd(ip,cmd)
    date_time_stamp = ""
    for line in output.split("\n"):
        line = line.strip()
        if line.isdigit() and len(line) == 14:
            date_time_stamp = line.strip()

    tarName = "tar -cvzf " + name + "_" + date_time_stamp +".tgz" + " webrtc_UAGC_*"
    mv_log = "mv *.tgz /data/automation_logs/"
    cmd = ["cd /data/storage/log","./stop_log.sh", tarName, mv_log]
    run_remote_cmd(ip,cmd)


def stop_logs_uplane(name):
    cmd = ["date '+%Y%m%d%H%M%S'"]
    output = run_remote_cmd(uplane_gm_ip,cmd)
    date_time_stamp = ""
    for line in output.split("\n"):
        line = line.strip()
        if line.isdigit() and len(line) == 14:
            date_time_stamp = line.strip()

    tarName = "tar -cvzf " + name + "_" + date_time_stamp +".tgz" + " webrtc_UAGC_*"
    mv_log = "mv *.tgz /data/automation_logs/"
    cmd = ["cd /data/storage/log","./stop_log.sh", tarName, mv_log]
    run_remote_cmd(uplane_gm_ip,cmd)

def getSipMsgtoCore(log_file_path):
    patt = "DBG.*sipMgr.*PSocket.*Len=\d+"
    ptt2 = "\<\d+:\d+:\d+\.\d{3}"
    sipMsgs = ""
    foundsipMsg = 0
    with open(log_file_path,"r") as fp:
        for line in fp:
            if foundsipMsg == 0:
                pattM = re.search(patt,line)
                if pattM:
                    foundsipMsg = 1
                    sipMsgs = sipMsgs + line
                    continue
            if foundsipMsg == 1:
                pattM2 = re.search(ptt2,line)
                pattM3 = re.search(patt,line)
                if not (pattM2 or pattM3):
                    sipMsgs = sipMsgs + line
                else:
                    foundsipMsg = 0

    return sipMsgs

def getMsrpMsgtoCore(log_file_path):
    patt_1 = "DBG WEBGW_SVC.*Sending Chat Message as a MSRP message to core ->"
    patt_2 = "DBG WEBGW_SVC.*Sending Geolocation Xml as a MSRP message to core ->"
    ptt2 = "\<\d+:\d+:\d+\.\d{3}"
    msrpMsgs = ""
    foundmsrpMsg = 0
    with open(log_file_path,"r") as fp:
        for line in fp:
            if foundmsrpMsg == 1:
                pattM2 = re.search(ptt2,line)
                if not pattM2:
                    msrpMsgs = msrpMsgs + line
                else:
                    foundmsrpMsg = 0
            if foundmsrpMsg == 0:
                pattM = re.search(patt_1,line)
                pattM1 = re.search(patt_2,line)
                if pattM:
                    foundmsrpMsg = 1
                    msrpMsgs = msrpMsgs + line
                    continue
                if pattM1:
                    foundmsrpMsg = 1
                    msrpMsgs = msrpMsgs + line
                    continue
    return msrpMsgs

def check_sip_method(sip_msg,sip_method):
    patt = "CSeq: [0-9]+ "+sip_method
    pattM = re.search(patt,sip_msg)
    if pattM:
        return 1
    else:
        return 0

def check_type_of_msg(sip_msg,type_of_msg):
    lineNumber = 0
    patt = "^SIP/2.0 "
    for line in sip_msg.split("\n"):
        lineNumber += 1
        if lineNumber == 2:
            pattM = re.search(patt,line)
            if pattM:
                if type_of_msg == "req":
                    return 0
                if type_of_msg == "res":
                    return 1
            else:
                if type_of_msg == "req":
                    return 1
                if type_of_msg == "res":
                    return 0


def check_direction(sip_msg,direction):
    lineNumber = 0
    for line in sip_msg.split("\n"):
        lineNumber += 1
        if lineNumber == 1:
            if line.find("<-") != -1:
                if direction == "in":
                    return 1
                else:
                    return 0
            if line.find("->") != -1:
                if direction == "out":
                    return 1
                else:
                    return 0

def check_call_id(single_sip_msg,call_id):
    if call_id == "null":
        return 1
    else:
        msg_call_id = gettheHeaderValue(single_sip_msg,"Call-ID")
        if msg_call_id == call_id:
            return 1
        else:
            return 0

def check_msrp_msg_id(single_msrp_msg,msg_id):
    if msg_id == "null":
        return 1
    else:
        imdn_msg_id = gettheHeaderValue(single_msrp_msg,"imdn.Message-ID")
        if imdn_msg_id == msg_id:
            return 1
        else:
            return 0

def check_haeaderVal(single_sip_msg,haeaderVal):
    if haeaderVal == "null":
        return 1
    else:
        if type(haeaderVal) == list and len(haeaderVal) == 2:
            msg_headervalue = gettheHeaderValue(single_sip_msg,haeaderVal[0])
            pattM = re.search(haeaderVal[1],msg_headervalue)
            if pattM:
                return 1
            else:
                return 0
        else:
            logging.error("Please check your argument header argument should be list with lenght 2")
            return 0

def check_msgTextVal(single_msrp_msg,textVal):
    patt = "^Content-Length: (.*)$"
    found = 0
    if textVal == "null":
        return 1
    else:
        for line in single_msrp_msg.split("\n"):
            if found == 1:
                pattM_1 = re.search(textVal,line);
                if pattM_1:
                    return 1
                else:
                    continue
            pattM = re.search(patt,line)
            if pattM:
                found = 1
    if found == 0:
        logging.error("Text is not found in the msrp message")
        return 0
                
###################################
#type_of_msg : req,res
#direction : in,out
#haeaderVal example : ["User-Agent","send 603"]
###################################
def getOnesipMsg(log_file_path,sip_method,Number,call_id="null",haeaderVal="null",type_of_msg="req",direction="out",interface="mw"):
    sip_number = 0
    sip_msgs = getSipMsgtoCore(log_file_path)
    patt = "DBG.*sipMgr.*PSocket.*Len=\d+"
    single_sip_msg = ""
    getMsg = 0
    found = 0
    for line in sip_msgs.split("\n"):
        if found == 0:
            pattM = re.search(patt,line)
            if pattM:
                found = 1
                single_sip_msg = single_sip_msg + line + "\n"
                continue
        if found == 1:
            pattM = re.search(patt,line)
            if pattM:
                if check_direction(single_sip_msg,direction):
                    if check_type_of_msg(single_sip_msg,type_of_msg):
                        if check_sip_method(single_sip_msg,sip_method):
                            if check_call_id(single_sip_msg,call_id):
                                if check_haeaderVal(single_sip_msg,haeaderVal):
                                    sip_number += 1
                                    if sip_number == Number:
                                        return single_sip_msg
                single_sip_msg = ""
                single_sip_msg = single_sip_msg + line + "\n"
            else:
                single_sip_msg = single_sip_msg + line + "\n"
    if not getMsg:
        logging.error("Desire sipMsg is not found in the logs Please check it manually")
        return 0


def getOnemsrpMsg(log_file_path,Number,msg_id="null",headerVal="null",msg_text="null"):
    msrp_number = 0
    msrp_msgs = getMsrpMsgtoCore(log_file_path)
    #logging.error(msrp_msgs)
    patt = "DBG WEBGW_SVC.*Sending.* as a MSRP message to core ->"
    patt_2 = "\<\d+:\d+:\d+\.\d{3}"
    single_msrp_msg = ""
    getMsg = 0
    found = 0
    for line in msrp_msgs.split("\n"):
        if found == 0:
            pattM = re.search(patt,line)
            if pattM:
                found = 1
                single_msrp_msg = single_msrp_msg + line + "\n"
                continue
        if found == 1:
            pattM = re.search(patt,line)
            if pattM :
                if check_msrp_msg_id(single_msrp_msg,msg_id):
                    if check_haeaderVal(single_msrp_msg,headerVal):
                        if check_msgTextVal(single_msrp_msg,msg_text):
                            msrp_number += 1
                            if msrp_number == Number:
                                return single_msrp_msg
                single_msrp_msg = ""
                single_msrp_msg = single_msrp_msg + line + "\n"
            else:
                single_msrp_msg = single_msrp_msg + line + "\n"

    if single_msrp_msg != "":
        if check_msrp_msg_id(single_msrp_msg,msg_id):
            if check_haeaderVal(single_msrp_msg,headerVal):
                if check_msgTextVal(single_msrp_msg,msg_text):
                    msrp_number += 1
                    if msrp_number == Number:
                        return single_msrp_msg
    if not getMsg:
        logging.error("Desire msrpMsg is not found in the logs Please check it manually")
        return 0


def gettheHeaderValue(sipMsg,headerName):
    patt = "^"+headerName+": (.*)$"
    found = 0
    lineNumber = 0
    for line in sipMsg.split("\n"):
        lineNumber += 1
        if headerName == "req-uri":
            if lineNumber == 2:
                return line.strip() 
        else:
            pattM = re.search(patt,line)
            if pattM:
                return pattM.group(1).strip()
    if found == 0:
        logging.error(headerName + " is not found in the sip message")
        return 0


def getContentSipMsg(sipMsg):
    found = 0
    sipContent = ""
    for line in sipMsg.split("\n"):
        pattM = re.search(r"^\s*$",line)
        if found == 1:
            sipContent = sipContent + line + "\n"
        elif pattM:
            found = 1
            sipContent = sipContent + line + "\n"
    return sipContent


def checkMediaValue(sipMsg,mediaAtt):
    sipContent = getContentSipMsg(sipMsg)
    #logging.info("this is sip content of msg")
    #logging.info(sipContent)
    if type(mediaAtt) == str:
        pattM = re.search(mediaAtt,sipContent)
        if pattM:
            logging.debug(mediaAtt + " is found in the sip message Content")
            return 1
        else:
            logging.error(mediaAtt + " is not found in the sip message Content")
            return 0
    if type(mediaAtt) == list:
        fail = 0
        for patt in mediaAtt:
            pattM = re.search(patt,sipContent)
            if pattM:
                logging.debug(patt + " is found in the sip message Content")
            else:
                logging.error(patt + " is not found in the sip message Content")
                fail += 1
        if not fail:
            return 1
        else:
            return 0

def getNsMsg(logfile,patt,msg_num=1):
    number = 0
    patt1 = "INF NOTIFY_SERVER.*sendNotifyMsg.*NotifyServerWebSocketSession.*nsMsg.*" + patt
    fn = open(logfile,"r+")
    for line in fn:
        pattM = re.search(patt1,line)
        if pattM:
            number += 1
            if number == msg_num:
                return line
    return 0

def getpushMsg(logfile,patt,msg_num=1):
    number = 0
    patt1 = "DBG.*dumpHttpReqInfo-LHttpRequest.*push-message.*" + patt
    fn = open(logfile,"r+")
    for line in fn:
        pattM = re.search(patt1,line)
        if pattM:
            number += 1
            if number == msg_num:
                return line
    return 0

def creatFinalResultFile(path):
    getLinuxOutput("rm -f " + path)
    getLinuxOutput("touch " + path)
    checkLogValidation(path)


def exit_script_mark_fail(file_path):
    cmd = "echo 'FAIL' > " + file_path
    getLinuxOutput(cmd)
    sys.exit()

def stopBinaryIAMScript():
    cmd = "kill -9 $(ps -ef|grep iam|grep -v grep |awk '{print $2}')"
    run_remote_cmd(db_ip,cmd)

def startBinaryIAMscript():
    cmd = ["cd /root/IAM","nohup ./iam_tmo -address 0.0.0.0:445 -timeout 300 >/dev/null 2>&1 &"]
    run_remote_cmd(db_ip,cmd)

def startMultiLineIAMscript(scriptname):
    cmd = ["cd /root/IAM_SSL"]
    cmd.append("nohup python "+scriptname+" &")
    run_remote_cmd(db_ip,cmd)

def stopPythonIAMScript():
    cmd  = "kill -9 $(ps -ef|grep testIAM.py|grep -v grep |awk '{print $2}')"
    run_remote_cmd(db_ip,cmd)

def cleanCplane_log():
    cmd = ["cd /data/storage/log","./cleanupPcapLogs.sh"]
    run_remote_cmd(node_gm_ip,cmd)

def getTimeStampofSipMsg(sipMsg):
    line = sipMsg.split("\n")[0]
    ptt = "\<(\d+:\d+:\d+\.\d{3}) "
    pattM = re.search(ptt,line)
    return pattM.group(1)

def checkCDRdecode():
    cmd = ["cd /data/redun/cdr/asn1","ls -lrt *ber"]
    output = run_remote_cmd(db_ip,cmd)
    files = []
    for line in output.split("\n"):
        ptt = re.search(r"Mavenir_CDR_PCSCF.*_A.ber",line)
        if ptt:
            files.append(ptt.group(0))
    
    error_file = []
    for file_name in files:
        cmd = "/data/redun/cdr/cdrDecoder.sh /data/redun/cdr/asn1/" + file_name
        output = run_remote_cmd(db_ip,cmd)
        for line in output.split("\n"):
            if "Find unknow element in the file,exit" in line or "Can not find tag" in line:
                error_file.append(file_name)
                break
            else:
                pass

    return error_file

def getrmtOutput(output):
    output = output.split("\n")
    output = output[1:]
    output = output[:-1]
    return "\n".join(output)

def killProcess(prc_name):
    cmd = "ps -ef|grep "+ prc_name +"|grep -v grep|awk '{print $2}'"
    output = run_remote_cmd(db_ip,cmd)
    proc_id = getrmtOutput(output)
    cmd = "kill -9 " + proc_id
    run_remote_cmd(db_ip,cmd)
    time.sleep(2)
    cmd = "ps -ef|grep "+prc_name+"|grep -v grep"
    output = run_remote_cmd(db_ip,cmd)
    pt = "start=warm"
    ptM = re.search(output,pt)
    if ptM:
        logging.debug(prc_name + "killed successfully")
        return 1
    else:
        logging.error(prc_name + "is not killed successfully")
        return 0


def checkSpace():
    cmd = "df -hk|grep vg_sda-data|awk '{print $5}'"
    output = run_remote_cmd(db_ip,cmd)
    output = getrmtOutput(output)
    output = output.replace("%","")
    if int(output) > 90:
        logging.error("Test Bed is having very less disk space Please clear the space and try")
        return 0
    else:
        logging.debug("Used space in test bed is " + output)
        return 1

def startMemTrace(ip,binaryName):
    cmd = 'export MAV_MEM_METHOD=malloc;export VALGRIND_LIB=/lib/valgrind; export LD_LIBRARY_PATH="/usr/IMS/current/bin:"$LD_LIBRARY_PATH'
    run_remote_cmd(ip,cmd)
    cmd = 'export VALGRIND_LIB=/usr/lib64/valgrind'
    run_remote_cmd(ip,cmd)
    cmd = "mv /usr/IMS/current/bin/" + binaryName + " /usr/IMS/current/bin/" + binaryName + "_val"
    run_remote_cmd(ip,cmd)
    #killing the given process
    cmd = "pkill -9 " + binaryName
    run_remote_cmd(ip,cmd)
    cmd = "nohup valgrind --leak-check=full --show-reachable=yes --error-limit=no --max-stackframe=8000000  --soname-synonyms=somalloc=libtcmalloc_minimal.so.4 --log-file=/root/val_"+binaryName+".log /usr/IMS/current/bin/"+binaryName+"_val >/dev/null 2>&1 &"

    run_remote_cmd(ip,cmd)
    
    time.sleep(10)

    cmd = "ps -ef|grep valgrind|grep -v grep|awk '{print $2}'"
    op = run_remote_cmd(ip,cmd)
    if op:
        logging.debug("valgrind is started successfully")
    else:
        logging.error("valgrind is not started Please check it manually")

def stopMemTrace(ip,binaryName):
    cmd = "ps -ef|grep valgrind|grep -v grep|awk '{print $2}'"
    op = run_remote_cmd(ip,cmd)
    op = getrmtOutput(op)
    if op:
        print "op >>>>",op
        cmd = "kill -9 " + op
        run_remote_cmd(ip,cmd)
        cmd = "mv /usr/IMS/current/bin/" + binaryName + "_val /usr/IMS/current/bin/" + binaryName
        run_remote_cmd(ip,cmd)
        cmd = "/usr/IMS/current/bin/"+binaryName
        run_remote_cmd(ip,cmd)
    else:
        logging.error("valgrind is not started Please check it manually")

######################################
#rFileName = "upc,sc,SIPRE,GTRE1,mp,FE
#
#####################################
def nfv_getLogs(ip,scp_path,rFileName = None,mode="log",path="/root/LOG_PCAP/automation_scripts"):
    if rFileName:
        if rFileName == "SIPRE" and mode == "log":
            sortSipMsgsofDiffFiles(ip,scp_path,path)
            return 1
        else:
            cmd = "cd "+path+";ls -lrt "+rFileName+"*"+"ACTIVE*"+mode+".gz|tail -n 1|awk '{print $9}'"
    else:
        cmd = "cd "+path+";ls -lrt *tgz|tail -n 1|awk '{print $9}'"
    op = run_remote_cmd(ip,cmd)
    op = getrmtOutput(op)
    filename = op.strip()
    cmd = "scp root@" + ip + ":" + path + "/" + filename + " " + scp_path
    #time.sleep(20)
    getscp_cmd(cmd)
    



def sortSipMsgsofDiffFiles(ip,scp_path,path):
    getLinuxOutput("rm -f /home/mavenir/SIPRE*ACTIVE*log")
    getLinuxOutput("rm -f /home/mavenir/SIPRE*ACTIVE*log.gz")
    cmd = "scp root@" + ip + ":"+ path + "/SIPRE*ACTIVE*log.gz /home/mavenir/"
    getscp_cmd(cmd)
    output = getLinuxOutput("ls -lrt /home/mavenir/SIPRE*ACTIVE*log.gz|awk '{print $9}'")
    files = output.split("\n")
    sipMsgs = ""
    for fileName in files:
        getLinuxOutput("gunzip "+fileName)
        fileName = fileName.replace(".gz","")
        sipMsgInFile = getSipMsgtoCore(fileName)
        sipMsgs = sipMsgs+sipMsgInFile
    sipMsgs = sipMsgs+"<13:00:39.226 DBG SIP 6783:7027 0:0><sipMgrUDPSocket:0-0-0-0>[send(sipMgrUDPSocket.cpp:151)] " \
                      "10.69.24.164:5062 -> 10.10.221.200:5092 Len=4185\n"
    found = 0
    patt = "DBG.*sipMgr.*PSocket.*Len=\d+"
    single_sip_msg = ""
    list_of_sipMsg = []

    for line in sipMsgs.split("\n"):
        if found == 0:
            pattM = re.search(patt,line)
            if pattM:
                found = 1
                single_sip_msg = single_sip_msg + line + "\n"
                continue
        if found == 1:
            pattM = re.search(patt,line)
            if pattM:
                timestamp = gettimeStampSipMsg(single_sip_msg)
                epoch_time = (timestamp - datetime(1970, 1, 1)).total_seconds()
                single_sip_msg = single_sip_msg + "<13:00:39.226 DBG SIP 6783:7027 0:0><sipMgrUDPSocket:0-0-0-0>\n"
                lista = [epoch_time,single_sip_msg]
                list_of_sipMsg.append(lista)
                single_sip_msg = ""
                single_sip_msg = single_sip_msg + line + "\n"
            else:
                single_sip_msg = single_sip_msg + line + "\n"

    list_of_sipMsg =  sorted(list_of_sipMsg, key=lambda x: x[0])
    sipMsg_final = ""
    finalFileName = scp_path + "/SIPRE_ACTIVE_.log"
    for i in list_of_sipMsg:
        sipMsg_final = sipMsg_final+i[1]

    sipMsg_final = sipMsg_final+"<13:00:39.226 DBG SIP 6783:7027 0:0><sipMgrUDPSocket:0-0-0-0>[send(sipMgrUDPSocket.cpp:151)] " \
                   "10.69.24.164:5062 -> 10.10.221.200:5092 Len=4185\n" 
    cmd = "echo '"+sipMsg_final+"' > "+finalFileName
    getLinuxOutput(cmd)
    getLinuxOutput("gzip "+finalFileName)

#########################################
#
#
#########################################
def nfv_dbChange(ip,cmd,node):
    cmdRun = "python /data/peerLvnScript/changeDb.py '"+cmd +"' " +node
    run_remote_cmd(ip,cmdRun)

def nfv_killProcess(ip,binary,node):
    cmdkill = "python /data/peerLvnScript/run_commmand.py \"killall -10 " + binary + "\" " +node 
    run_remote_cmd(ip,cmdkill)

def gettimeStampSipMsg(sipMsg):
    line1 = sipMsg.split("\n")[0]
    ptt = "\<(\d+:\d+:\d+\.\d{3}) "
    pattM = re.search(ptt,line1)
    timeStamp = pattM.group(1)
    FMT = '%H:%M:%S.%f'
    epochTime = datetime.strptime(timeStamp,FMT)
    return epochTime

def checkDbValue(ip,cmd,node_ip):
    cmdRun = "python /data/peerLvnScript/useAppcommon.py \"getDBoutput('"+node_ip+"','"+cmd+"')\""
    op = run_remote_cmd(ip,cmdRun)
    logging.debug(op)
    pattM = re.search("syntax error: unknown argument",op)
    if pattM:
        logging.error("Expected values are not present in the configuration")
        return 0
    data_value = {}
    counter = 0
    for line in op.split("\n"):
        if counter == 1:
            pattM = re.search("^\[ok\]",line)
            if pattM:
                counter = 0
            else:
                a = line.split()
                data_value[a[0]] = a[1]
        else:
            pattM = re.search(" show table sys",line)
            if pattM:
                counter = 1

    return data_value

def checkhttpRequest(logfile,headerPatt,msgNum = 1):
    fp = open(logfile,"r")
    httpCounter = 0
    msgCounter = 0
    httpMsg = ""
    for line in fp:
        if httpCounter == 1:
            if not line.strip():
                if re.search(headerPatt,httpMsg):
                    msgCounter += 1
                    if msgCounter == msgNum:
                        return httpMsg
                httpCounter = 0
                httpMsg = ""
            else:
                httpMsg = httpMsg + line
        if re.search("^Hypertext Transfer Protocol",line):
            httpCounter = 1
            httpMsg = httpMsg + line
    
    if msgCounter == 0:
        logging.error("HTTP message "+headerPatt+" is not found in the pcap")
        return 0


def gethttpHeader(httpMsg,header):
    for line in httpMsg.split('\n'):
        pattM = re.search(header+":(.*)",line)
        if pattM:
            return pattM.group(1).strip()
    
    
def checkKeyword(logfile,key):
    fp = open(logfile,"r")
    for line in fp:
        if re.search(key,line):
            return 1
    return 0

def getJsonvalue(httpMgs,keyvalue):
    patt = "Key: "+keyvalue
    prevline = ""
    current = ""
    jvalue = []

    for line in httpMgs.split('\n'):
        currLine = line
        if prevline == "":
            prevLine = line
        
        if re.search(patt,currLine):
            pattM = re.search(r'String value: (.*)$',prevline)
            if pattM:
                value = pattM.group(1)
                jvalue.append(value)
        prevline = currLine

    if len(jvalue) > 1:
        return jvalue
    elif len(jvalue) == 1:
        return jvalue[0]
    else:
        return 0

def getJson(httpMsg):
    jsonMsg = ""
    patt = "JavaScript Object Notation: application/json"
    found = 0
    for line in httpMsg.split('\n'):
        if found == 1:
            jsonMsg = jsonMsg + line
        if re.search(patt,line):
            jsonMsg = jsonMsg + line
            found = 1
    return jsonMsg

def checkLogValidation(fpath):
    if enable_logs == 0:
        cmd = "echo PASS > "+fpath
        getLinuxOutput(cmd)
        sys.exit()

def nfv_getCoreDetail(ip,mode):
    cmd = "checkCore |grep core|grep -v stacktrace |awk '{print $9}'|sort"
    op = run_remote_cmd(ip,cmd)
    op = getrmtOutput(op)
    if op:
        f_op = op
    else:
        f_op = ""

    if mode == "before":
        f = open("/tmp/beforeCore.txt","w")
        f.write(f_op)
    elif mode == "after":
        f = open("/tmp/afterCore.txt","w")
        f.write(f_op)

def nfv_checkCore():
    f1 = open("/tmp/beforeCore.txt","r")
    f2 = open("/tmp/afterCore.txt","r")
    before = f1.read()
    after = f2.read()
    before = list(map(str.strip,before.split('\n')))
    after = list(map(str.strip,after.split('\n')))
    diff = list(set(before) - set(after))
    if len(diff):
        return diff
    else:
        return 0


def start_pcrf(pcrf_ip, xml_name):
    stop_pcrf(pcrf_ip)
    cmd = "cd /root/RX/AAR_Prov_signaling_flow;export LD_LIBRARY_PATH=/usr/local/bin;/usr/local/bin/seagull -conf conf_server.xml  " \
          "-dico base_rx.xml  -scen {}.xml -log /root/log/Arjun_RAR_Specific_Action_release_brearer_abort_cause1.log " \
          "-llevel ETMA  -bg".format(xml_name)
    run_remote_cmd(pcrf_ip, cmd)
    time.sleep(2)


def stop_pcrf(pcrf_ip):
    cmd = "pkill -9 seagull"
    run_remote_cmd(pcrf_ip, cmd)
    time.sleep(2)


##################################################
#use of funtion : to send the Email from gmail
#arguments : to , this should be list of string or string 
#txtfile , this should be mail content
#refernce script path : scripts/LVN_script/healthcheck.py 
#################################################
def sendEmailfromGmail(to,txtfile):
    server=smtplib.SMTP("smtp.gmail.com",587)
    server.starttls()
    server.login("load.mailer@gmail.com","load1234")
    server.sendmail("load.mailer@gmail.com",to,txtfile)
    server.quit()


def getNdStoreTrlInfo(rmtIP,nodeName):
    #def run_remote_cmd(ip,cmds,username = "root",passw="mavenir",tmout = 200):
    cmd = "rmtCmd 'ls -lrt /data/redun/cdr/trl/*/*/* |grep Mavenir_TRL |tail -n 10' "+ nodeName +"| awk '{print $9}'  > /data/peerLvnScript/tmp_" + nodeName
    run_remote_cmd(rmtIP,cmd)


def getTrlData(rmtIP,nodeName):
    cmds = ["cd /data/peerLvnScript/","python getDecodTRL.py "+nodeName]
    op = run_remote_cmd(rmtIP,cmds)
    return op

def decodeTRLData(a):
    JsonData = ""
    finalData = {}
    tag = ""
    for line in a.split("\n"):
        #if "EventBuffer" in line:
        #    break
        if line:
            line = line.strip()
            patt = re.search("(.*) {$",line)
            if patt:
                temp_tag = patt.groups()[0].strip()
                if tag:
                    tag = tag + "-" + temp_tag
                else:
                    tag = temp_tag
            elif line.strip() == "}":
                if tag:
                    b = tag.split("-")
                    tag = "-".join(b[:-1])
	                
            else:
                pattd = re.search("(.*?) : (.*)",line)
                if pattd:
                    mKey = pattd.groups()[0].strip()
	            if tag:
	                fKey = tag + "-" + mKey
	            else:
	                fKey = mKey
                    mValue = pattd.groups()[1].strip()
                    finalData[fKey] = mValue

    return finalData

#############################
#arguments : ip which is remote node addres in case of NFV it is CMS 
#nodeName : nodeName you need to give as per your setup for VDF
#"sc" means WRG
#"uag" means ASCVNF
#it will get the KPI logs and copies in local sever as
#/root/LOG_PCAP/automation_scripts/KPI.txt
############################
def getKPIvalue(ip,nodeName):
    getLinuxOutput(">/home/mavenir/automation/Cdigit/common/scripts/checkKPI/KPI.txt")    
    cmd = 'zgrep --no-filename "TMM.*setCounter" /root/LOG_PCAP/automation_scripts/'+nodeName+'* > /root/LOG_PCAP/automation_scripts/KPI.txt'
    output = run_remote_cmd(ip,cmd)
    getscp_cmd("scp root@"+ip+":/root/LOG_PCAP/automation_scripts/KPI.txt /home/mavenir/automation/Cdigit/common/scripts/checkKPI/KPI.txt")    
#####################
#it will check the KPI value from KPI file which is copied locally
#arguments: counterGrp means counte grp Name such as REG_DEV or REG_SUB
#counterName : for example INITIAL_REGISTER_ATT
#return value is string for example '1','0'
#but if nothing is found then it will retrun 0 (integer) 
################
def checkKPI(counterGrp,counterName,freq = 1,gauge = "no"):
    with open("/home/mavenir/automation/Cdigit/common/scripts/checkKPI/KPI.txt", 'r') as fp:
        op = fp.read()
        patt = "TMM.*tmmClient.*setCounter.*\("+counterGrp+"\), objId=.*?,(.*?), counterID=.* \("+counterName+"\), number=(.*?),"
        found = 0
        for line in op.split("\n"):
            pt = re.search(patt,line)
            if pt:
                found += 1
                if found == freq:
                    grp = pt.groups()[0]
                    value = pt.groups()[1]
                    return value
    return 0


def parseCdr(data,sipMethod,cdr_parse):
    patt = "(.*)::.*Value=(.*)"
    patt2 = "(.*)::Tag.*"
    patt3 = "^}"
    keyword = sipMethod
    for line in data.split("\n"):
        line = line.strip()
        patM = re.search(patt,line)
        patM2 = re.search(patt2,line)
        patM3 = re.search(patt3,line)
        if patM:
            key,value = patM.groups()
            tmpKey = keyword + "_" + key
            cdr_parse[tmpKey] = value
        elif patM2:
            key = patM2.groups()[0]
            keyword = keyword + "_" + key
        elif patM3:
            keyword = "_".join(keyword.split("_")[:-1])
    return cdr_parse


def getsipMethod(data):
    patt = "sIP-Method::.*Value=(.*)"
    sipMethod = None
    for line in data.split("\n"):
        patM = re.search(patt,line)
        if patM:
            
            sipMethod = patM.groups()[0]
            break
    return sipMethod


def parseCDRFile(fileName):
    fd = open(fileName,"r")
    cdr_parse = {}
    sipM = ""
    found = 0
    cdrdata = ""
    for line in fd:
        if line:
            if "wEBRTCRecord" in line:
                if found == 1:
                    sipM = getsipMethod(cdrdata)
                    cdr_parse = parseCdr(cdrdata,sipM,cdr_parse)
                    cdrdata = ""
                    sipM = ""
                else:
                    found = 1
                    continue
            if found == 1:
                if "wEBRTCRecord" not in line:
                    cdrdata = cdrdata + line
    sipM = getsipMethod(cdrdata)
    cdr_parse = parseCdr(cdrdata,sipM,cdr_parse)

    return cdr_parse

def checkCDRvalues(cdrfile,vFile):
    cdr_parse = parseCDRFile(cdrfile)
    validate_parse = parseCDRFile(vFile)

    for key in cdr_parse:
        patt = re.search(validate_parse[key],cdr_parse[key])
        if patt:
            logging.debug("{} value is matching as expected".format(key))
        else:
            logging.error("{} value is not matching as expected .. Expected is {} but found {}".format(key,validate_parse[key],cdr_parse[key]))
