import os
import sys
import re
import argparse
import time
import zipfile

blacklist=[]

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def timestr(time):
    return bcolors.OKBLUE+str(time)+bcolors.ENDC

def numstr(num):
    return bcolors.OKGREEN+str(num)+bcolors.ENDC

print "scanning binary package...."
start_time = time.time()
binarypath = ''
for file in os.listdir('.'):
    fileName, fileExt = os.path.splitext(file)
    if fileExt == '.ipa':
        zippack = zipfile.ZipFile(file)
        apppath = zippack.namelist()[1][:-1]#Payload/QQ.app
        appname = os.path.splitext(os.path.basename(apppath))[0]
        binarypath = os.path.join(apppath,appname)#Payload/QQ.app/QQ
        zippack.extract(binarypath, '')
        break
print 'binarypath: %s' %binarypath
referedselectors = os.popen('otool -v -s __DATA __objc_selrefs '+binarypath).read()
os.system('rm -rf Payload')
print "done scanning binary package."
print "costs: %s seconds ---" %(timestr(time.time() - start_time))


print "scanning selector list...."
contentarmv7 = None
contentarm64 = None
for file in os.listdir('.'):
    fileName, fileExt = os.path.splitext(file)
    if 'armv7' in fileName:
        f = open(file,"r")
        contentarmv7 = f.read()
        f.close()
    if 'arm64' in fileName:
        f = open(file,"r")
        contentarm64 = f.read()
        f.close()
if contentarmv7 and contentarm64:
    pass
else:
    print bcolors.FAIL+"linkmap files not exist."+bcolors.ENDC
    sys.exit()


start_time = time.time()

selectorlist = []
selectorlistarm64 = []
selectorpattern = "(0x\w+)\t\[\s*(\d+)\]\s[+|\-]\[(\w+\s(.+))\]\n"
matchlist = re.findall(selectorpattern,contentarmv7)
matchlistarm64 = re.findall(selectorpattern, contentarm64)
index = 0
for match in matchlist:
    index = index+1
    sizeinbyte = str(int(match[0],16))
    targetid = match[1]
    classandselector = match[2]
    selector = match[3]
    targetpattern = "\n\[\s*"+targetid+"\]\s\/.+\/(.+)"
    targetname = re.search(targetpattern,contentarmv7).group(1)
        
    #search for size in arm64
    sizeinbytearm64 = 0
    for matcharm64 in matchlistarm64:
        if classandselector == matcharm64[2]:
            sizeinbytearm64 = str(int(matcharm64[0],16))
            matchlistarm64.remove(matcharm64)
            break

    selectorlist.append((targetname,sizeinbyte,sizeinbytearm64,selector))
    sys.stdout.write("\r%s selector scaned       " % numstr(index))

print "\ndone scanning selector list...."
print "costs: %s seconds ---" %(timestr(time.time() - start_time))
start_time = time.time()

print "filter system selectors...."

f = open("iOS_api_list.txt","r")
systemselectors = f.read()
f.close()
count = 0
filterdselectorlist = []
for selector in selectorlist:
    selectorname = selector[3]
    if selectorname not in systemselectors:
        filterdselectorlist.append(selector)
    else:
        count = count + 1
selectorlist = filterdselectorlist

print "done filter system selectors, filterd %s system call back" %(numstr(count))
print "costs: %s seconds ---" %(timestr(time.time() - start_time))

print "scanning for unused selectors...."
index = 0
count = 0
staticcount = 0
result = ""
staticlibresult = ""


for selector in selectorlist:
    index = index+1
    objectfilename = selector[0]
    sizeinbytearmv7 = selector[1]
    sizeinbytearm64 = selector[2]
    selectorname = selector[3]
    shouldignore = False
    for ignore in blacklist:
        if ignore in selectorname:
            shouldignore = True
            break
    if shouldignore:
        continue
    if selectorname not in referedselectors:
        temp = '\t'.join((objectfilename,sizeinbytearmv7,sizeinbytearm64,selectorname))+'\n'
        if '(' in objectfilename:
            staticcount = staticcount + 1
            staticlibresult = staticlibresult + temp
        else:
            count = count + 1
            result = result + temp
    sys.stdout.write("\r%s selector scaned       " % numstr(index))

title = "File\tSize armv7\tSize arm64\tMethod\n"

f1 = open("result.txt","w")
f2 = open("staticlibresult.txt","w")
f1.write(title)
f1.write(result)
f2.write(title)
f2.write(staticlibresult)
f1.close()
f2.close()
print "\ndone scanning for unused selectors."
print "costs: %s seconds ---" %(timestr(time.time() - start_time))
print "--- Total unused selector found: %s, %s ---" %(numstr(count), numstr(staticcount))
