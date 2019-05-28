# -*- coding: utf-8 -*-

import os
import os.path
import sys
import time
import shutil

rootdir = "api"
pythonstr = ""
isModuleAPI = False
ignoreKeys = ["属性文档", "回调函数文档", "成员函数文档"]


def findDocsFiles():
	files = []

	for parent, dirnames, filenames in os.walk(rootdir):
		for filename in filenames:
			f = parent + "\\" + filename
			if ".htm" in filename and ("Classes"  in parent  or "Modules"  in parent):
				files.append(f)

	return files

def modifyDatas(prefix, data):
	data = data.replace("&nbsp;", " ").replace("\r", "")
	data = data.replace("&lt;", "〈").replace("&gt;", "〉")
	#data = data.rstrip()

	data.replace(r"""<br>""", "\n")

	while True:
		i = data.find("<")
		if i < 0:
			break
		
		ii = data.find(">", i)
		
		if ii > 0:
			data = data.replace(data[i : ii + 1], "")

	if len(data) == 0:
		return ""

	return prefix + data

def parseFunctions(data, substate):
	global pythonstr
	global isModuleAPI

	if substate == 0:
		if r"""<div class="function_description">""" in data:
			substate = 1
			data = modifyDatas(isModuleAPI + "\t", data)
			pythonstr += data
			if len(data) > 0 and not isModuleAPI:
				data += "\t"
	elif substate == 1:
		if r"""definition">""" in data:
			substate = 4
		else:
			if r"""</div>""" in data:
				substate = 2
			else:
				pythonstr += modifyDatas(isModuleAPI + "\t", data)

	elif substate == 2:
		if r"""definition">""" in data:
			substate = 4
		else:
			if r"""</table>""" in data:
				substate = 3
			else:
				hasArgTitle = "function_parameter_name" in data
				if hasArgTitle:
					hasArgTitle = "@"
				else:
					hasArgTitle = ""

				pythonstr += modifyDatas(isModuleAPI + "\t" + hasArgTitle, data)
	else:
		if r"""definition">""" in data:
			substate = 4
		else:
			pythonstr += modifyDatas(isModuleAPI + "\t", data)

	return substate

def parseAttributes(data, substate):
	global pythonstr
	global isModuleAPI
	
	if substate == 0:
		if r"""<div class="attribute_description">""" in data:
			substate = 1
			pythonstr += modifyDatas(isModuleAPI + "\t", data)
	elif substate == 1:
		if r"""definition">""" in data:
			substate = 2
		else:
			if r"""</div>""" in data:
				substate = 2
			else:
				pythonstr += modifyDatas(isModuleAPI + "\t", data)

	return substate

def writeTipsPy(processName, moduleName, datas):
	dirstr = "tips/" + processName + "/"

	try:
		os.makedirs(dirstr)
	except:
		pass

	f = open(dirstr + moduleName + ".py", "a+", encoding="UTF-8")
	f.write(datas)
	f.close()
	print("save to: %s/%s.py" % (os.getcwd(), dirstr + moduleName))

def parseDocs(f):
	print("====>parseDocs(): " + f + "...")

	temp = f.replace("\\","/")
	fd = open(temp, "r", encoding="UTF-8")
	lines = fd.readlines()
	fd.close()

	# 主状态1：分析方法
		# 子状态1：分析主描述
		# 子状态2：分析参数描述
		# 子状态3：分析返回值描述
		# 子状态4：分析结束
	# 主状态2：分析属性
		# 子状态1：分析主描述
		# 子状态2：分析结束
	# 主状态3：分析子类
		# 子状态1：分析主描述
		# 子状态2：分析结束

	state = 0
	substate = 0

	global pythonstr
	global isModuleAPI

	moduleDocs = ""
	pythonstr = ""
	isModuleAPI = "Modules" in f
	processName = temp.split("/")[1]
	moduleName = os.path.basename(f).split(".")[0]

	if not isModuleAPI:
		isModuleAPI = "\t"
		moduleDocs += "class " + moduleName + ":\n"
	else:
		isModuleAPI = ""
	
	for data in lines:
		for key in ignoreKeys:
			if key in data:
				state = 0
				substate = 0
				continue
			
		#print("%i---%i--%s" % (state, substate, pythonstr))
	
		if state == 0:
			if len(pythonstr) > 0:
				pythonstr += "\n\t" + isModuleAPI + "\"\"\"\n\t" + isModuleAPI + "pass" +"\n\n"
				moduleDocs += pythonstr

			pythonstr = ""
			if r"""<span class="function_definition">""" in data:
				pythonstr = modifyDatas(isModuleAPI, data)

				if len(pythonstr) > 0 and pythonstr[-1] == "\n":
					pythonstr = pythonstr[0 : len(pythonstr) - 1]
					
				state = 1
				pythonstr += "\n\t" + isModuleAPI + "\"\"\""
				
			elif r"""<span class="attribute_definition">""" in data:
				pythonstr = isModuleAPI + "@property\n"
				pythonstr += modifyDatas(isModuleAPI + "def ", data)
				
				if len(pythonstr) > 0 and pythonstr[-1] == "\n":
					pythonstr = pythonstr[0 : len(pythonstr) - 1]

				if len(isModuleAPI) > 0:
					pythonstr += "( self ):\n"
				else:
					pythonstr += "():\n"
				pythonstr += "\n\t" + isModuleAPI + "\"\"\""
				state = 2
		elif state == 1:
			substate = parseFunctions(data, substate)
			if substate == 4:
				substate = 0
				state = 0
		else:
			substate = parseAttributes(data, substate)
			if substate == 2:
				substate = 0
				state = 0

	if len(pythonstr) > 0:
		pythonstr += "\n\t" + isModuleAPI + "\"\"\"\n\t" + isModuleAPI + "pass" +"\n\n"
		pythonstr = pythonstr.replace("版权归KBEngine所有。", "")
		moduleDocs += pythonstr

	writeTipsPy(processName, "KBEngine", moduleDocs)

def generatePythonTips():
	print("generatePythonTips: start...")

	try:
		shutil.rmtree(r'tips') 
	except:
		pass

	files = findDocsFiles()

	for f in files:
		parseDocs(f)

	print("generatePythonTips: over!")
	
if __name__ == "__main__":
	generatePythonTips()
