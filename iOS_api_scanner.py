
import os
import sys
import re
import time
import operator
import argparse
import threading

sdkFrameworkDir = "/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk/System/Library/Frameworks"

blacklist = []

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def removeCommentLine(content):
    result = re.sub(r'^\/\/.*?$','',content,flags=re.M) #multiline mode: ^...$ match one line
    result = re.sub(r'\/\*.*?\*\/','',result,flags=re.S)
    return result

def scanHeaderFile():
    methodlist = []
    headerfilecontent = ""
    for framework in os.listdir(sdkFrameworkDir):
        headerDir = os.path.join(sdkFrameworkDir, framework, "Headers")
        if os.path.exists(headerDir):
            for file in os.listdir(headerDir):
                fullpath = os.path.join(headerDir,file)
                if os.path.isdir(fullpath):
                    verboseprint1(file)
                    continue
                f = open(fullpath,"r")
                fulltext = f.read()
                content = removeCommentLine(fulltext)
                headerfilecontent = headerfilecontent + "\n" + content
                f.close()
    methods = re.findall(r'-\s*\([\w *&]+\)\s*((?:.+?\n*)+?)(?: (?:NS_.+|__TVOS.+))?;[\s\n]*',headerfilecontent,re.M)
        
    verboseprint2(methods)
    for methodName in methods:
        verboseprint2(methodName)
        methodName = methodName.strip()
        if ":" in methodName:
            temp = re.findall(r'(\S*?)\s*:\s*\(.+?\)\s*\w+',methodName)
            #remove space
            map(str.strip, temp)
            methodName = ":".join(temp) + ":"
        if len(methodName) and (methodName not in methodlist):
            methodlist.append(methodName)
        else:
            verboseprint2("Warning: same method definition found: %s" % methodName)
    verboseprint1("%d methods found...." % len(methodlist))

    return methodlist




parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="increase output verbosity", type=int, choices=[0, 1, 2])
args = parser.parse_args()

if args.verbose == 2:
    def verboseprint1(*args):
        # Print each argument separately so caller doesn't need to
        # stuff everything to be printed into a single string
        for arg in args:
            print arg,
        print
    def verboseprint2(*args):
        for arg in args:
            print arg,
            print
elif args.verbose == 1:
    def verboseprint1(*args):
        for arg in args:
            print arg,
        print
    verboseprint2 = lambda *a: None      # do-nothing function
else:
    verboseprint1 = lambda *a: None      # do-nothing function
    verboseprint2 = lambda *a: None      # do-nothing function

start_time = time.time()
methodlist = scanHeaderFile()
print("--- Scanning header costs: %s seconds ---" % (time.time() - start_time))
start_time = time.time()
if len(methodlist):
    resultFile = open("iOS_api_list.txt","w")
    for method in methodlist:
        resultFile.write(method+"\n")
    resultFile.flush()
    resultFile.close()

print("--- Writing file costs: %s seconds ---" % (time.time() - start_time))
print("--- Total API found: %d ---" %(len(methodlist)))
