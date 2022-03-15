#!/bin/python
#owner : arjungupta1@mavenir.com
'''
Usage:
1. this script is used to decode vEPC xml files 
Please give command line argument like\n 
            -h<hour> <group-name> e.g -h5 "EGTPC Sessions"\n 
            -m<min> <group-name> e.g -m30 "EGTPC Sessions"\n
            -m<min> -f <\"formula-name\"> e.g -m30 -f "Total S1U ING Data SGW"\n
            -h<hour> \"General:MaxCpu\" <userLabel> e.g -h4 "General:MaxCpu" SAEGW-CDF
Date: 17/1/2019
'''

import sys,getopt
import re
import time
import os
import subprocess
import xml.etree.ElementTree as ET
import operator
import datetime
import itertools


csvPath = "/root/KPI_tool/KPI_CSV/KPI_formulas_v20_VIL.csv"
counts_file_path = "/opt/VCM/etc/counters/3gpp"

arg_apn = None
timeZone = "UTC"
g_time1 = None
g_time2 = None
g_summary = None
g_frt = None
arg_idx = None
g_delta = False
sleepTime = 0.025
maxInstance = 5

def getaddedInstance(valueA):
	final_valueA = {}
	for key in valueA:
		temp_dic = {}
		for val in valueA[key]:
			value,instance = val.split("_")
			value = int(value)
			instance = int(instance)
			if instance not in temp_dic:
				temp_dic[instance] = value
			else:
				temp_dic[instance] = temp_dic[instance] + value

		for t_key in sorted(temp_dic.keys()):
			if key not in final_valueA:
				final_valueA[key] = [temp_dic[t_key]]
			else:
				final_valueA[key].append(temp_dic[t_key])
	
	return final_valueA

##############################################################
#getCounterValuefromFile
#xml_file : input single xml file name, type is string 
#group: type string, counter group Name
#based of give group name this function will fetch all the values from the xml file
#it will return the value of a couneter grp in dictionary data structure
###############################################################
def getCounterValuefromFile(group,xml_file,apn=None):
	counters = []
	valueA = {}
	vnfc_type = "instance"
	tree = ET.parse(xml_file)
	root = tree.getroot()
	found = 0	

	ns = {'spec':'http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec'}

	for measData in root.findall('spec:measData',ns):
		for measInfo in measData.findall('spec:measInfo',ns):
			if measInfo.attrib['measInfoId'] == group:
				for measType in measInfo.findall('spec:measType',ns):
					counters.append(measType.text)


	for measData in root.findall('spec:measData',ns):
		for measInfo in measData.findall('spec:measInfo',ns):
			if found == 1:
				break;
			if measInfo.attrib['measInfoId'] == group:
				found = 1
				for measValue in measInfo.findall('spec:measValue',ns):
					if "Instance" in measValue.attrib['measObjLdn']:
						vnfc_type = (measValue.attrib['measObjLdn'].split('=')[1]).split(',')[0]
						instance = (measValue.attrib['measObjLdn'].split('=')[2]).split(',')[0]
						if apn and (apn == getApnName(measValue.attrib['measObjLdn'])):
							for indx,values in enumerate(measValue.findall('spec:r',ns)):
								if counters[indx] not in valueA:
									valueA[counters[indx]] = [int(values.text)]
								else:
									valueA[counters[indx]].append(int(values.text))
						elif not apn:
							for indx,values in enumerate(measValue.findall('spec:r',ns)):
								if counters[indx] not in valueA:
									valueA[counters[indx]] = [values.text+"_"+instance]
								else:
									valueA[counters[indx]].append(values.text+"_"+instance)
	
	if not apn:	
		valueA = getaddedInstance(valueA)
	if not valueA:
		for counter in counters:
			valueA[counter] = [0]
	return valueA,vnfc_type


def getMaxCpuValuefromFile(group,userLabel,xml_file):
	counters = []
	valueA = {}

	tree = ET.parse(xml_file)

	root = tree.getroot()

	ns = {'spec':'http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec'}

	for measData in root.findall('spec:measData',ns):
		for managedElement in measData.findall('spec:managedElement',ns):
			if managedElement.attrib['userLabel'] == userLabel:
				for measInfo in measData.findall('spec:measInfo',ns):
					if measInfo.attrib['measInfoId'] == group:
						for measType in measInfo.findall('spec:measType',ns):
							counters.append(measType.text)


	for measData in root.findall('spec:measData',ns):
		for managedElement in measData.findall('spec:managedElement',ns):
			if managedElement.attrib['userLabel'] == userLabel:
				for measInfo in measData.findall('spec:measInfo',ns):
					if measInfo.attrib['measInfoId'] == group:
						for measValue in measInfo.findall('spec:measValue',ns):
							if "Instance" in measValue.attrib['measObjLdn']:
								vnfc_type = (measValue.attrib['measObjLdn'].split('=')[1]).split(',')[0]
								for indx,values in enumerate(measValue.findall('spec:r',ns)):
									if counters[indx] not in valueA:
										valueA[counters[indx]] = [int(values.text)]
									else:
										valueA[counters[indx]].append(int(values.text))
	if not valueA:
		for counter in counters:
			valueA[counter] = 0
	return valueA,vnfc_type


def getApnName(value):
	list_a = value.split(",")
	for val in list_a:
		if "ApnName" in val:
			f_value = val.split("=")[-1]
			return f_value
	

def getFormat(number):
    format_str = "{:<50}"
    for i in range(1,number):
            format_str = format_str + "  {:<20}"

    return format_str


def get_header(number,vnfc_type):
    header = "Counter_Name"
    for i in range(1,number):
        if i == (number - 1):
            header = header + " TOTAL"
        else:
            header = header + " " + vnfc_type +str(i)
    return header     


def get_formula_header(number,vnfc_type):
	header = "stime etime formula_name"
	number = number+1
	for i in range(1,number):
		if i == (number - 1):
			header = header + " summary"
		else:
			header = header + " "+vnfc_type+str(i)
	return header
	


def printCounter(group,final_dict,vnfc_type):
    print "==============================================="
    print group
    print "Time Interval: from {} to {}".format(g_time1,g_time2)
    print "==============================================="
    len_of_header = 0
    for keys in final_dict:
        line = keys + ' ' +' '.join(map(str,final_dict[keys])) + ' ' + str(sum(final_dict[keys]))
        word = line.split()
        len_of_header = len(word)
        break
    
    header = get_header(len_of_header,vnfc_type)
    format_str = getFormat(len_of_header)
    header = header.split()
    print(format_str.format(*header))
    
    for keys in final_dict:
        line = keys + ' ' +' '.join(map(str,final_dict[keys])) + ' ' + str(sum(final_dict[keys]))
        word = line.split()
        format_str = getFormat(len(word))
        print(format_str.format(*word))

def getFinalvalueList(values):
	f_val = []
	for val in values:
		x = [val[0],val[1],val[4]]+val[3]
		f_val.append(x)
	return f_val
		
		

def printFormulaIdxVrt(values):
	t1,t2,group,list_val,formula_name,vnfc_type = values[0]
	len_of_header = len(values[0][3])
	header = get_formula_header(len_of_header,vnfc_type)
	header = header.split()
	f_val = getFinalvalueList(values)
	for c_val in f_val:
		print "===================================="
		for i,val in enumerate(c_val):
			print "{:<20} {:<20}".format(header[i],c_val[i])

def printFormulaIdx(values):
	#group,list_val,formula_name,vnfc_type):
	if g_summary == "true":
		t1,t2,group,list_val,formula_name,vnfc_type = values[0]
		len_of_header = len(values[0][3])
		header = get_formula_header(1,vnfc_type)
		header = header.split()
		format_str = getFormat(len(header))
		format_str = format_str.split()
		format_str[0] = "{:<15}"
		format_str[1] = "{:<15}"
		format_str[2] = "{:<30}"
		format_str = " ".join(format_str)
		print(format_str.format(*header))
		for t_val in values:
			tmp1 = t_val[0]
			tmp2 = t_val[1]
			list_val = t_val[3]
			line = tmp1+' '+tmp2+' '+formula_name +' ' + str(list_val[-1])
			word = line.split()
			print(format_str.format(*word))
		
	else:
		if g_frt == "true":
			printFormulaIdxVrt(values)
		else: 
			t1,t2,group,list_val,formula_name,vnfc_type = values[0]
			len_of_header = len(values[0][3])
			header = get_formula_header(len_of_header,vnfc_type)
			header = header.split()
			format_str = getFormat(len(header))
			format_str = format_str.split()
			format_str[0] = "{:<15}"
			format_str[1] = "{:<15}"
			format_str[2] = "{:<30}"
			format_str = " ".join(format_str)
			print(format_str.format(*header))
			for t_val in values:
				tmp1 = t_val[0]
				tmp2 = t_val[1]
				list_val = t_val[3]
				line = tmp1+' '+tmp2+' '+formula_name +' ' +' '.join(map(str,list_val))
				word = line.split()
				print(format_str.format(*word))



def printFormula(group,list_val,formula_name,vnfc_type):
	#print "==============================================="
	#print group
	#print "Time Interval: from {} to {}".format(g_time1,g_time2)
	#print "==============================================="
	if g_summary == "true":
		header = get_formula_header(1,vnfc_type)
		header = header.split()
		format_str = getFormat(len(header))
		format_str = format_str.split()
		format_str[0] = "{:<15}"
		format_str[1] = "{:<15}"
		format_str[2] = "{:<30}"
		format_str = " ".join(format_str)
		print(format_str.format(*header))
		line = g_time1+' '+g_time2+' '+formula_name +' ' + str(list_val[-1])
		word = line.split()
		print(format_str.format(*word))	
	else:
		formula_name = formula_name.split()
		formula_name = "_".join(formula_name)
		len_of_header = len(list_val)
	
		header = get_formula_header(len_of_header,vnfc_type)
		header = header.split()
		format_str = getFormat(len(header))
		format_str = format_str.split()
		format_str[0] = "{:<15}"
		format_str[1] = "{:<15}"
		format_str[2] = "{:<30}"
		format_str = " ".join(format_str)
		print(format_str.format(*header))
		line = g_time1+' '+g_time2+' '+formula_name +' ' +' '.join(map(str,list_val))
		word = line.split()
		print(format_str.format(*word))



def getLinuxOutput(cmd):
    p = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=True)
    stdout,stderr= p.communicate()
    return stdout.strip()



##############################################################################
#Funtion Name : get_delta_dict
#input arguments : xml_file ,this can have 1 file or 2 file (start and end)
#group : This will give the information about the counter group
#Type : This will give value of Type of Counter , default value is CC
#This funtion provides the delta of stats of files if g_delta flag is true 
#than this fucntion will add the values of all files of give time interval
#return value is calculated dictionary which has values mapped to keys(counters)
###############################################################################

def get_delta_dict(xml_files,group,Type="CC"):
	final_dict = {}

	if Type == "GAUGE":
		if len(xml_files) == 1:
			xml_file = xml_files[0]
			final_dict,vnfc_type = getCounterValuefromFile(group,xml_file,arg_apn)
			return final_dict,vnfc_type
		else:
			xml_file = xml_files[1]
			final_dict,vnfc_type = getCounterValuefromFile(group,xml_file,arg_apn)
			return final_dict,vnfc_type
		
	if len(xml_files) == 1:
		xml_file = xml_files[0]
		final_dict,vnfc_type = getCounterValuefromFile(group,xml_file,arg_apn)
		return final_dict,vnfc_type

	if g_delta == False:
	
		for idx,xml_file in enumerate(xml_files):
			if idx == 0:
				valueB,vnfc_type = getCounterValuefromFile(group,xml_file,arg_apn)
			else:
				valueA,vnfc_type = getCounterValuefromFile(group,xml_file,arg_apn)
		for key in valueA:
			if len(valueA[key]) == len(valueB[key]):
				final_dict[key] =  list(map(operator.sub,valueA[key],valueB[key]))
			else:
				if len(valueA[key]) > len(valueB[key]):
					len_diff = len(valueA[key]) - len(valueB[key])
					for i in range(len_diff):
						valueB[key].append(0)
					final_dict[key] =  list(map(operator.sub,valueA[key],valueB[key]))
				elif len(valueB[key]) > len(valueA[key]):
					len_diff = len(valueB[key]) - len(valueA[key])
					for i in range(len_diff):
						valueA[key].append(0)
					final_dict[key] =  list(map(operator.sub,valueA[key],valueB[key]))	
		return  final_dict,vnfc_type

	# new condition is introduce to add the counter for given timestamps based on start and end files 

	elif g_delta == True:
		xml_files = getallxmlfiles(xml_files)
		for idx,xml_file in enumerate(xml_files):
			if idx == 0:
				final_dict,vnfc_type = getCounterValuefromFile(group,xml_file,arg_apn)
			else:
				valueA,vnfc_type = getCounterValuefromFile(group,xml_file,arg_apn)
				
				for key in valueA:	
					if len(valueA[key]) == len(final_dict[key]):
						final_dict[key] =  list(map(operator.add,valueA[key],final_dict[key]))
					else:
						if len(valueA[key]) > len(final_dict[key]):
							len_diff = len(valueA[key]) - len(final_dict[key])
							for i in range(len_diff):
								final_dict[key].append(0)
								time.sleep(sleepTime)
							final_dict[key] =  list(map(operator.add,valueA[key],final_dict[key]))

						elif len(final_dict[key]) > len(valueA[key]):
							len_diff = len(final_dict[key]) - len(valueA[key])
							for i in range(len_diff):
								final_dict[key].append(0)
								time.sleep(sleepTime)
							final_dict[key] =  list(map(operator.add,valueA[key],final_dict[key]))
					time.sleep(sleepTime)
			time.sleep(sleepTime)

		return  final_dict,vnfc_type
						
			
			
######################################################
#Function Name : checkFormulaInCsv
#argument : formula_name , Name of the formula
#usage : to check command line given formula is valid or not
######################################################
def checkFormulaInCsv(formula_name):
	#print formula_name
	check_counter = 0
	fp = open(csvPath,"r")
	for line in fp:
		line = line.split(",")
		if formula_name == line[1]:
			check_counter = 1
			return check_counter
	return check_counter


		
def getFormulaValues(formula_name):
	fp = open(csvPath,"r")
	for line in fp:
		line = line.split(",")
		if formula_name == line[1]:
			return line



def getnumeratorDenominator(final_dict,Numerator):
	Numerator = list(map(str.strip,Numerator.split("+")))
	final_num_value = []
	len_final_num_value = 0

	for keys in final_dict:
		len_final_num_value = len(final_dict[keys])
		break
	for i in range(len_final_num_value):
		final_num_value.append(0)
	
	if len(Numerator) > 1:
		for Num in Numerator:
			final_num_value = list(map(operator.add,final_num_value,final_dict[Num]))
			
		return final_num_value
	else:
		return final_dict[Numerator[0]]



def getAvgofgetnumeratorDenominator(final_dict,Numerator):
	Numerator = list(map(str.strip,Numerator.split("+")))
	final_add_value = []
	final_avg_value = []
	len_final_add_value = 0

	for keys in final_dict:
		len_final_add_value = len(final_dict[keys])
		break
	for i in range(len_final_add_value):
		final_add_value.append(0)
	
	for Num in Numerator:
		final_add_value = list(map(operator.add,final_add_value,final_dict[Num]))
			
	for value in final_add_value:
		tmp = operator.truediv(value,len(Numerator))
		tmp = round(tmp,2)
		final_avg_value.append(tmp)
	return final_avg_value
			


def checkfile(fileName):
    cmd = "ls "+fileName + " 2> /dev/null"
    #output = getLinuxOutput(cmd)
    output = os.popen(cmd).read().strip()
    if output:
        return output
    else:
        return 0


def checkfile_timestamp(ts,stime = 0):
	for i in range(25):
		tempts = ts
		timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M')
		if stime == 1:
			str_name = counts_file_path+"/A"+str(timestamp)[0:8]+"\."+str(timestamp)[-4:] + "*"
		else:
			if str(timestamp)[-4:] == "0000":
				temp_timestamp = tempts - 86400
				temp_timestamp = datetime.datetime.fromtimestamp(temp_timestamp).strftime('%Y%m%d%H%M')
				str_name = counts_file_path+"/A"+str(temp_timestamp)[0:8]+"*-"+str(timestamp)[-4:] + "*"
			else:
				str_name = counts_file_path+"/A"+str(timestamp)[0:8]+"*-"+str(timestamp)[-4:] + "*"
		
		output =  checkfile(str_name)
		if output:
			return output
		#if stime == 1:
		#	ts = ts + 60
		#else:
		#	ts = ts - 60
		ts = ts - 60
		time.sleep(sleepTime)


def getArgumentvalue(arg,list_val):
	i = 0
	for indx,value in enumerate(list_val):
		if value == arg:
			i = indx
			break
	if i == 0:
		return None
	
	return list_val[i+1]



def getFormulaList():
	f = open(csvPath,"r")
	for line in f:
		list_val = []
		line = line.split(",")
		list_val.append(line[1])
		list_val.append(line[10].rstrip())
		format_str = "{:<50} {:<10}"
		print(format_str.format(*list_val))



def setTimeZone():
	global timeZone
	#output = getLinuxOutput("date | awk '{print $5}'")
	output = os.popen("date | awk '{print $5}'").read()
	timeZone = output.strip()



def getFilesWithendandstartTime(stime,etime):
	output = ""
	if len(etime) == 12:
		ts  = (datetime.datetime(int(etime[:4]),int(etime[4:6]),int(etime[6:8]),int(etime[8:10]),int(etime[10:12])) - datetime.datetime(1970,1,1)).total_seconds()
		if timeZone == "IST":
			ts = ts - 19800
		str1 = checkfile_timestamp(ts)
		
	else:
		print "etime is not correct"
		sys.exit()
	if len(stime) == 12:
		ts  = (datetime.datetime(int(stime[:4]),int(stime[4:6]),int(stime[6:8]),int(stime[8:10]),int(stime[10:12])) - datetime.datetime(1970,1,1)).total_seconds()
		if timeZone == "IST":
			ts = ts - 19800
		str2 = checkfile_timestamp(ts,stime=1)
	else:
		print "stime is not correct"
		sys.exit()

	if str1 == str2:
		output = str1
	else:
		if str1 and str2:
			output = str2+"\n"+str1
		if str1 and not str2:
			output = str1

	return output	



def getepochTime(timeStamp):
	if len(timeStamp) == 12:
		ts  = (datetime.datetime(int(timeStamp[:4]),int(timeStamp[4:6]),int(timeStamp[6:8]),int(timeStamp[8:10]),int(timeStamp[10:12])) - datetime.datetime(1970,1,1)).total_seconds()
		if timeZone == "IST":
			ts = ts - 19800
		return ts

	else:
		print "timeStamp {} is not correct".format(timeStamp)
		sys.exit()


def setTimeInterval(xml_files):
	global g_time1
	global g_time2
	
	
	patt = "A(.*?)\+\d{4}\-(\d{4})"
	if len(xml_files) > 1:
		file_name = xml_files[0].strip()
		file_name = file_name.split("/")[-1]
		pattM = re.search(patt,file_name)
		t1 = pattM.group(1).split(".")
		g_time1 = t1[0]+":"+t1[1]

		file_name = xml_files[1].strip()
		file_name = file_name.split("/")[-1]
		pattM = re.search(patt,file_name)
		t2 = pattM.group(1).split(".")
		g_time2 = t2[0]+":"+pattM.group(2)
		
	else:
		file_name = xml_files[0].strip()
		file_name = file_name.split("/")[-1]
		pattM = re.search(patt,file_name)
		t1 = pattM.group(1).split(".")
		#g_time1 = ":".join(t1)
		g_time1 = t1[0]+":"+t1[1]
		
		g_time2 = t1[0]+":"+pattM.group(2)
		
		



def setTimeIntervalmin(t_min):
	global g_time1
	global g_time2
	ts = time.time()
	g_time1 = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d:%H%M')
	t_min = int(t_min)*60
	ts = ts - int(t_min)
	g_time2 = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d:%H%M')



def setTimeIntervalStartEnd(stime,etime):
	global g_time1
	global g_time2
	g_time1 = stime[:8]+ ":"+stime[8:10]+stime[10:12]
	g_time2 = etime[:8]+ ":"+etime[8:10]+etime[10:12]



def getvaluefromFormula(arg_formula,xml_files):
	formula_name = arg_formula
	formula_name = formula_name.strip()	
	if checkFormulaInCsv(formula_name):
		values = getFormulaValues(formula_name)
		if values[1]:formula_name = values[1]
		if values[2]:sub_system = values[2]
		if values[3]:VNFC = values[3]
		if values[4]:group = values[4]
		if values[5]:Type = values[5]
		if values[6]:
			sub_type = values[6]
		else:
			sub_type = "null"
		if values[7]:Numerator = values[7]
		if values[8]:
			Denominator = values[8]
		else:
			Denominator = "null"
		if values[9]:
			Summary = values[9]
		else:
			Summary = "null"
				
		final_dict,vnfc_type = get_delta_dict(xml_files,group,Type)

		numerator_stats = getnumeratorDenominator(final_dict,Numerator)

		if Denominator != "null" and sub_type != "Custom":
			denominator_stats = getnumeratorDenominator(final_dict,Denominator)

		
		if Type == "GAUGE" and sub_type == "null":
			list_val = numerator_stats
			list_val.append(sum(list_val))
			return (group,list_val,formula_name,vnfc_type)
	
		if Type == "GAUGE" and sub_type == "Percentage":
			list_val = []
			tmp_val = numerator_stats
			tmp_val.append(sum(tmp_val))
			denominator_stats.append(sum(denominator_stats))	
			for i in range(len(numerator_stats)):
				if denominator_stats[i] == 0:
					val = "("+str(numerator_stats[i])+"/"+str(denominator_stats[i])+")"+"0.0"+"%"
					list_val.append(val)
				else:
					tmp = operator.truediv(numerator_stats[i],denominator_stats[i])
					tmp_val = round(tmp*100,2)
					val = "("+str(numerator_stats[i])+"/"+str(denominator_stats[i])+")"+str(tmp_val)+"%"
					list_val.append(val)
				time.sleep(sleepTime)
			return (group,list_val,formula_name,vnfc_type)	
				
		if Type == "CC" and sub_type == "Percentage":
			list_val = []
			#print "numerator_stats", numerator_stats
			#print "denominator_stats", denominator_stats
			for i in range(len(numerator_stats)):
				if denominator_stats[i] == 0:
					val = "("+str(numerator_stats[i])+"/"+str(denominator_stats[i])+")"+"0.0"+"%"
					list_val.append(val)
				else:
					tmp = operator.truediv(numerator_stats[i],denominator_stats[i])
					tmp_val = round(tmp*100,2)
					val = "("+str(numerator_stats[i])+"/"+str(denominator_stats[i])+")"+str(tmp_val)+"%"
					list_val.append(val)
				time.sleep(sleepTime)

			sum_numerator_stats = sum(numerator_stats)
			sum_denominator_stats = sum(denominator_stats)
			if sum_denominator_stats == 0:
				summary = 0.0
				val = "("+str(sum_numerator_stats)+"/"+str(sum_denominator_stats)+")"+str(summary)+"%"
				list_val.append(val)
			else:
				summary = operator.truediv(sum_numerator_stats,sum_denominator_stats)
				summary = round(summary*100,2)
				val = "("+str(sum_numerator_stats)+"/"+str(sum_denominator_stats)+")"+str(summary)+"%"
				list_val.append(val)	
			
			return (group,list_val,formula_name,vnfc_type)
	
		if Type == "CC" and sub_type == "Average":
			list_val = []
			avg_stat = getAvgofgetnumeratorDenominator(final_dict,Numerator)
			list_val = avg_stat
			
			summary = sum(avg_stat)
			tmp = operator.truediv(summary,len(avg_stat))
			tmp = round(tmp,2)
			list_val.append(tmp)
			return (group,list_val,formula_name,vnfc_type)
			
		if Type == "CC" and sub_type == "Cumulative":
			
			list_val = numerator_stats
			list_val.append(sum(list_val))
			return (group,list_val,formula_name,vnfc_type)
		
		if Type == "CC" and sub_type == "Custom":
			list_val = []
			tmp_val = numerator_stats
			tmp_val.append(sum(tmp_val))
			if Denominator.isdigit():
				for val in tmp_val:
					val = val /float(Denominator)
					val = round(val,4)
					list_val.append(val)
					time.sleep(sleepTime)
				return (group,list_val,formula_name,vnfc_type)
			else:
				if "time" in Denominator:
					time = gettimediif(xml_files)
					Denominator = Denominator.replace("<$time>",str(time))
					Denominator = eval(Denominator)
					for val in tmp_val:
						val = val /float(Denominator)
						val = round(val,4)
						list_val.append(val)
					return (group,list_val,formula_name,vnfc_type)

		if Type == "CC" and sub_type == "null":
			list_val = []
			tmp_val = numerator_stats
			tmp_val.append(sum(tmp_val))
			if Denominator != "null":
				denominator_stats.append(sum(denominator_stats))
				for i in range(len(numerator_stats)):
					if denominator_stats[i] == 0:
						val = "("+str(numerator_stats[i])+"/"+str(denominator_stats[i])+")"+"0"
						list_val.append(val)
					else:
						tmp = operator.truediv(numerator_stats[i],denominator_stats[i])
						tmp_val = round(tmp,2)
						val = "("+str(numerator_stats[i])+"/"+str(denominator_stats[i])+")"+str(tmp_val)
						list_val.append(val)
					time.sleep(sleepTime)
				return (group,list_val,arg_formula,vnfc_type)
			else:
				list_val = tmp_val
				return (group,list_val,arg_formula,vnfc_type)

		
	else:
		print "Formula is not present in the csv"
		sys.exit()




def getvaluefromFormulaofFormula(arg_formula,xml_files):
	formula_name = arg_formula
	formula_name = formula_name.strip()	
	if checkFormulaInCsv(formula_name):
		values = getFormulaValues(formula_name)
		if values[1]:formula_name = values[1]
		if values[2]:sub_system = values[2]
		if values[3]:VNFC = values[3]
		if values[4]:group = values[4]
		if values[5]:Type = values[5]
		if values[6]:
			sub_type = values[6]
		else:
			sub_type = "null"
		if values[7]:Numerator = values[7]
		if values[8]:
			Denominator = values[8]
		else:
			Denominator = "null"
		if values[9]:
			Summary = values[9]
		else:
			Summary = "null"
		
		list_val_num = []
		patt = "\$([\w\-]+) "
		patt1 = "\$([\w\-]+)$"
		numForluma_list = re.findall(patt,Numerator)
		numForluma_list.append(re.search(patt1,Numerator).group(1))

		for formula in numForluma_list:
			group,list_val,formula_name,vnfc_type = getvaluefromFormula(formula,xml_files)
			list_val_num.append(list_val)
			time.sleep(sleepTime)
		
		numerator_stats = [sum(x) for x in zip(*list_val_num)]
		numerator_stats.pop()
	
		if Denominator != "null" and sub_type != "Custom":
			list_val_den = []
			patt = "\$([\w\-]+) "
			patt1 = "\$([\w\-]+)$"
			denForluma_list = re.findall(patt,Denominator)
			denForluma_list.append(re.search(patt1,Denominator).group(1))

			for formula in denForluma_list:
				group,list_val,formula_name,vnfc_type = getvaluefromFormula(formula,xml_files)
				list_val_den.append(list_val)
				time.sleep(sleepTime)
				
			denominator_stats = [sum(x) for x in zip(*list_val_den)]
			denominator_stats.pop()

		if Type == "GAUGE" and sub_type == "null":
			list_val = numerator_stats
			list_val.append(sum(list_val))
			return (group,list_val,arg_formula,vnfc_type)
	
		if Type == "GAUGE" and sub_type == "Percentage":
			list_val = []
			tmp_val = numerator_stats
			tmp_val.append(sum(tmp_val))
			denominator_stats.append(sum(denominator_stats))	
			for i in range(len(numerator_stats)):
				if denominator_stats[i] == 0:
					val = "("+str(numerator_stats[i])+"/"+str(denominator_stats[i])+")"+"0.0"+"%"
					list_val.append(val)
				else:
					tmp = operator.truediv(numerator_stats[i],denominator_stats[i])
					tmp_val = round(tmp*100,2)
					val = "("+str(numerator_stats[i])+"/"+str(denominator_stats[i])+")"+str(tmp_val)+"%"
					list_val.append(val)
				time.sleep(sleepTime)
			return (group,list_val,arg_formula,vnfc_type)	
				
		if Type == "CC" and sub_type == "Percentage":
			list_val = []
			#print "numerator_stats", numerator_stats
			#print "denominator_stats", denominator_stats
			for i in range(len(numerator_stats)):
				if denominator_stats[i] == 0:
					val = "("+str(numerator_stats[i])+"/"+str(denominator_stats[i])+")"+"0.0"+"%"
					list_val.append(val)
				else:
					tmp = operator.truediv(numerator_stats[i],denominator_stats[i])
					tmp_val = round(tmp*100,2)
					val = "("+str(numerator_stats[i])+"/"+str(denominator_stats[i])+")"+str(tmp_val)+"%"
					list_val.append(val)
				time.sleep(sleepTime)

			sum_numerator_stats = sum(numerator_stats)
			sum_denominator_stats = sum(denominator_stats)
			if sum_denominator_stats == 0:
				summary = 0.0
				val = "("+str(sum_numerator_stats)+"/"+str(sum_denominator_stats)+")"+str(summary)+"%"
				list_val.append(val)
			else:
				summary = operator.truediv(sum_numerator_stats,sum_denominator_stats)
				summary = round(summary*100,2)
				val = "("+str(sum_numerator_stats)+"/"+str(sum_denominator_stats)+")"+str(summary)+"%"
				list_val.append(val)	
			
			return (group,list_val,arg_formula,vnfc_type)
	
		if Type == "CC" and sub_type == "Average":
			list_val = []
			avg_stat = getAvgofgetnumeratorDenominator(final_dict,Numerator)
			list_val = avg_stat
			
			summary = sum(avg_stat)
			tmp = operator.truediv(summary,len(avg_stat))
			tmp = round(tmp,2)
			list_val.append(tmp)
			return (group,list_val,arg_formula,vnfc_type)
			
		if Type == "CC" and sub_type == "Cumulative":
			
			list_val = numerator_stats
			list_val.append(sum(list_val))
			return (group,list_val,arg_formula,vnfc_type)
		
		if Type == "CC" and sub_type == "Custom":
			list_val = []
			tmp_val = numerator_stats
			tmp_val.append(sum(tmp_val))
			if Denominator.isdigit():
				for val in tmp_val:
					val = val /float(Denominator)
					val = round(val,4)
					list_val.append(val)
					time.sleep(sleepTime)
				return (group,list_val,arg_formula,vnfc_type)
			else:
				if "time" in Denominator:
					time = gettimediif(xml_files)
					Denominator = Denominator.replace("<$time>",str(time))
					Denominator = eval(Denominator)
					for val in tmp_val:
						val = val /float(Denominator)
						val = round(val,4)
						list_val.append(val)
						time.sleep(sleepTime)
					return (group,list_val,arg_formula,vnfc_type)

		if Type == "CC" and sub_type == "null":
			list_val = []
			tmp_val = numerator_stats
			tmp_val.append(sum(tmp_val))
			if Denominator != "null":
				denominator_stats.append(sum(denominator_stats))
				for i in range(len(numerator_stats)):
					if denominator_stats[i] == 0:
						val = "("+str(numerator_stats[i])+"/"+str(denominator_stats[i])+")"+"0"
						list_val.append(val)
					else:
						tmp = operator.truediv(numerator_stats[i],denominator_stats[i])
						tmp_val = round(tmp,2)
						val = "("+str(numerator_stats[i])+"/"+str(denominator_stats[i])+")"+str(tmp_val)
						list_val.append(val)
					time.sleep(sleepTime)
				return (group,list_val,arg_formula,vnfc_type)
			else:
				list_val = tmp_val
				return (group,list_val,arg_formula,vnfc_type)
	else:
		print "Formula is not present in the csv"
		sys.exit()


def gettimediif(xml_files):
	if len(xml_files) == 1:
		patt = "A(.*?)\+\d{4}\-(\d{4})"
		file_name = xml_files[0].strip()
		pattM = re.search(patt,file_name)
		timeV = pattM.group(1).split(".")
		t1 = timeV[0] + timeV[1]
		t2 = timeV[0]+pattM.group(2)
		time1 = getepochTime(t1)
		time2 = getepochTime(t2)
		if re.search("A.*\-0000",file_name):
			time2 = time2 + 86400
		return time2 - time1

	else:
		patt = "A(.*?)\+\d{4}\-(\d{4})"
		file_name = xml_files[0].strip()
		file_name = file_name.split("/")[-1]
		pattM = re.search(patt,file_name)
		timeV = pattM.group(1).split(".")
		t1 = timeV[0] + timeV[1]
		time1 = getepochTime(t1)

		file_name = xml_files[1].strip()
		file_name = file_name.split("/")[-1]
		pattM = re.search(patt,file_name)
		t2 = pattM.group(1).split(".")
		t2 = t2[0]+pattM.group(2)
		time2 = getepochTime(t2)
		if re.search("A.*\-0000",file_name):
			time2 = time2 + 86400

		return time2 - time1


def getvaluefromGroup(arg_group,xml_files):
			group = arg_group
			if group == "General:MaxCpu":
				userLabel = arg_userLabel
				if len(xml_files) > 1:
					xml_file = xml_files[1]
				else:
					xml_file = xml_files[0]
				final_dict,vnfc_type = getMaxCpuValuefromFile(group,userLabel,xml_file)
				return (group,final_dict,vnfc_type)	
			else:
				final_dict,vnfc_type = get_delta_dict(xml_files,group)
				return (group,final_dict,vnfc_type)

def checkTypeisFormula(arg_formula):
	line = getFormulaValues(arg_formula)
	if line[4] == "Formula":
		return 1	


def getValuesfromXmlFile(output):
	xml_files = []	
	xml_files.append(output[0])
	if len(output) > 1:
		xml_files.append(output[-1])
	if xml_files:
		if "-f" in arg_dict:
			if checkTypeisFormula(arg_formula):
				group,list_val,formula_name,vnfc_type = getvaluefromFormulaofFormula(arg_formula,xml_files)	
			else:
				group,list_val,formula_name,vnfc_type = getvaluefromFormula(arg_formula,xml_files)

			if arg_idx == "time":
				setTimeInterval(output)
				return g_time1,g_time2,group,list_val,formula_name,vnfc_type
			else:
				setTimeInterval(output)
				final_val = [(g_time1,g_time2,group,list_val,formula_name,vnfc_type)] 
				printFormulaIdx(final_val)
	
		elif "-g" in arg_dict:
			group,final_dict,vnfc_type = getvaluefromGroup(arg_group,xml_files)
			printCounter(group,final_dict,vnfc_type)			
	else:
		print "No XML file is generated for the given time period"
		sys.exit()



def getallxmlfiles(output):
	sfile = output[0]
	efile = output[1]
	all_xml_files = []
	patt = "A([0-9]{8})\.([0-9]{4})\+"
	patM = re.search(patt,sfile)
	stime = patM.group(1)+patM.group(2)
	ts  = (datetime.datetime(int(stime[:4]),int(stime[4:6]),int(stime[6:8]),int(stime[8:10]),int(stime[10:12])) - datetime.datetime(1970,1,1)).total_seconds()
	if timeZone == "IST":
		ts = ts - 19800

	currentfile = sfile
	while (currentfile != efile):
		timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M')
		str_name = counts_file_path+"/A"+str(timestamp)[0:8]+"."+str(timestamp)[-4:] + "*"
		#print str_name
		output =  checkfile(str_name)
		if output:
			all_xml_files.append(output)
			currentfile = output
		ts = ts + 60
		time.sleep(sleepTime)
	
	return all_xml_files

def validateInputTime(stime,etime):
	ts_etime = (datetime.datetime(int(etime[:4]),int(etime[4:6]),int(etime[6:8]),int(etime[8:10]),int(etime[10:12])) - datetime.datetime(1970,1,1)).total_seconds()
	ts_stime = (datetime.datetime(int(stime[:4]),int(stime[4:6]),int(stime[6:8]),int(stime[8:10]),int(stime[10:12])) - datetime.datetime(1970,1,1)).total_seconds()
	if ts_etime > ts_stime:
		return 1
	else:
		print "stime is greater than the etime"
		return 0


def usage():
	print """
	-hour       this option will give delta of stats of last given hours
	-min 	    this option will give delta of stats of last given mins
	-f          to give formula name
	-g          to give gorup name
	-stime      option for start time
	-etime      option for end time
	-userLabel  option to give userLabel for General:MaxCpu
	            userLabel can have values : SAEGW-EIF,SAEGW-CPE,SAEGW-DPE,SAEGW-VEM,SAEGW-CDF,SAEGW-SDB
	-list       option to show all formula present in the csv.
	-apn        option to give APN name.
	-idx        option to get the output from all files in given time. This should have value "time"
	-frt        option to get the output vertically. It should have value "v"
	-summary    option to print only summary of the output. it should have value "true"
	-delta		option to calculate CC counters interval based. It should have value "true"

	e.g.        ./agg_kpi_v11.py -f Total_Subs_SGW -stime 201901181321 -etime 201901181421
	            ./agg_kpi_v11.py -g "APN: Control Plane" -stime 201901181321 -etime 201901181421 -apn apn1
	            ./agg_kpi_v11.py -min 60 -f GTP_Create_Session_SR_PGW
	            ./agg_kpi_v11.py -hour  1 -g "EGTPC Sessions" 
	            ./agg_kpi_v11.py -hour 2 -g General:MaxCpu -userLabel SAEGW-CPE
	            ./agg_kpi_v11.py -f Total_GBR_UL_Data_Mbps -hour 1  -frt v
	            ./agg_kpi_v11.py -f Total_GBR_UL_Data_Mbps -hour 1 -idx time
	            ./agg_kpi_v11.py -f Total_GBR_UL_Data_Mbps -hour 1 -idx time -frt v
             	./agg_kpi_v10.py -delta true -f Total_Def_Bearer_SGW -stime 202005081216 -etime 202005081226 -delta true"""
#---------------------------------------------------------------------------------------------------------

#xml_files = []

try:
	scriptName = os.path.basename(__file__).strip().replace(".py","")
	output = os.popen("ps -ef|grep "+ scriptName + "|grep -v grep |awk '{print $2}'").read().strip()
	if output:
		if len(output.split("\n")) > maxInstance:
			print maxInstance,"instances of script are running already wait for sometime or kill old one"
			sys.exit()
		
	
	setTimeZone()
	if sys.argv[1] == "-list":
		getFormulaList()
		sys.exit()
	
	del sys.argv[0]
	arg_dict = dict(itertools.izip_longest(*[iter(sys.argv)] * 2, fillvalue=""))
	
	############
	#argument veriables
	############ 
	
	if "-hour" in arg_dict and "-min" in arg_dict:
		print "you have given both hour and min argument. Please correct argument"
		sys.exit()
	if "-g" in arg_dict and "-f" in arg_dict:
		print "you have given both -f and -g argument. Please correct argument"
		sys.exit()
	
	if (("-stime" in arg_dict) and ("-etime" in arg_dict)) and not(("-hour" in arg_dict) or ("-min" in arg_dict)):
		pass
	elif "-hour" in arg_dict or "-min" in arg_dict:
		pass
	else:
		print "you have given wrong argument. Either stime or etime is missing OR hour and min is also given"
		sys.exit()

	if ("-g" in arg_dict and  arg_dict['-g'] == "General:MaxCpu" and not("-userLabel" in arg_dict)):
		print "Please give -userLabel argument too"
		sys.exit()	

	if "-hour" in arg_dict:arg_hour = arg_dict['-hour']
	if "-min" in arg_dict:arg_min = arg_dict['-min']
	if "-g" in arg_dict:arg_group = arg_dict['-g']
	if "-f" in arg_dict:arg_formula = arg_dict['-f']
	if "-stime" in arg_dict:arg_stime = arg_dict['-stime']
	if "-etime" in arg_dict:arg_etime = arg_dict['-etime']
	if "-userLabel" in arg_dict:arg_userLabel = arg_dict['-userLabel']
	if "-apn" in arg_dict:arg_apn = arg_dict['-apn']
	if "-idx" in arg_dict:arg_idx = arg_dict['-idx']
	if "-summary" in arg_dict:arg_summary = arg_dict['-summary']
	if "-frt" in arg_dict:arg_frt = arg_dict['-frt']
	if "-delta" in arg_dict:arg_delta = arg_dict['-delta']


	if "-delta" in arg_dict and arg_delta == "true" :
		g_delta = True
		print "g_delta is set True"

	if "-frt" in arg_dict and arg_frt == "v":
		#global g_frt
		g_frt = "true"

	if "-summary" in arg_dict:
		g_summary = arg_summary	

	if "-hour" in arg_dict:
		t_min = str(int(arg_hour) * 60)
		setTimeIntervalmin(t_min)

	if "-min" in arg_dict:
		t_min = arg_min
		setTimeIntervalmin(t_min)

	if 't_min' in locals():
		ts = time.time()
		timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M')
		str1 = checkfile_timestamp(ts)
		t_min = int(t_min)*60
		ts = ts - t_min
		timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M')
		str2 =checkfile_timestamp(ts,1)
	
		if str1 == str2:
			output = str1
		else:
			if str1 and str2:
					output = str2+"\n"+str1
			if str1 and not str2:
				output = str1
	
	if ("-stime" in arg_dict) and ("-etime" in arg_dict) and validateInputTime(arg_stime,arg_etime):
		if len(arg_stime) == 12 and len(arg_etime) == 12:
			setTimeIntervalStartEnd(arg_stime,arg_etime)
			etime = arg_etime
			stime = arg_stime
			output = getFilesWithendandstartTime(stime,etime)
		else:
			print "Please give valid -stime and -etime"
			
	if (not 'output' in locals()) or (not output):
		print "No XML files are found for given period"
		sys.exit()
 	
	output = output.split("\n")
			
	if "-idx" in arg_dict and arg_idx == "time" and "-f" in arg_dict:
		all_xml_file = getallxmlfiles(output)
		final_values = []
		prev = 0
		current = 1
		if g_delta == True:
			for indx,files in enumerate(all_xml_file):
				files = [files]
				values  = getValuesfromXmlFile(files)
				final_values.append(values)
			printFormulaIdx(final_values)
			
		else: 
			for indx,files in enumerate(all_xml_file):
				if current == len(all_xml_file):
					break
				else:	
					files = [all_xml_file[prev],all_xml_file[current]]
					#group,list_val,formula_name,vnfc_type
					values  = getValuesfromXmlFile(files)
					final_values.append(values)
					prev += 1
					current += 1
			printFormulaIdx(final_values)
	else:
		getValuesfromXmlFile(output)

		
except IndexError:
	usage()

