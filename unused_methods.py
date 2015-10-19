
import os
import sys
import re
import time
import operator
import argparse
import threading

projectfilelist = ["QQMSFContact.xcodeproj/project.pbxproj",
               "Classes/engine/QQ/FileCenter/project.pbxproj",
               "Classes/engine/QQ/FileCenter/WeiyunSDK.xcodeproj/project.pbxproj",
               "Classes/engine/QQ/FileCenter/WYQQAlbumBackupSDK/WYQQAlbumBackupSDK.xcodeproj/project.pbxproj",
               "Classes/extern/ProtoBuff/protobuff.xcodeproj/project.pbxproj",
               "Classes/module/CardExchangeModule/CardExchangeModule.xcodeproj/project.pbxproj",
               "Classes/module/Contacts/Contacts.xcodeproj/project.pbxproj",
               "Classes/module/DiscussGroup/DiscussGroup.xcodeproj/project.pbxproj",
               "Classes/module/DynamicFace/DynamicFace.xcodeproj/project.pbxproj",
               "Classes/module/FileTransfer/qlink/library/xplatform/projects/xcode/xplatform.xcodeproj/project.pbxproj",
               "Classes/module/FileTransfer/qlink/projects/xcode/qlink/qlink.xcodeproj/project.pbxproj",
               "Classes/module/liteTransfer/build/xcode/litetransfer/litetransfer.xcodeproj/project.pbxproj",
               "Classes/module/LuaWaxEngine/LuaWaxEngine.xcodeproj/project.pbxproj",
               "Classes/module/MQQReader_Mini/QQReader.xcodeproj/project.pbxproj",
               "Classes/module/QMusic/QMusic.xcodeproj/project.pbxproj",
               "Classes/module/QQComic/QQComic.xcodeproj/project.pbxproj",
               "Classes/module/QQUIComponents/LEGO.xcodeproj/project.pbxproj",
               "Classes/module/QQVideoChatModule/QQVideoChatModule.xcodeproj/project.pbxproj",
               "Classes/module/QZone/QZone/engineV2/JCEProtocol/JCEProtocol.xcodeproj/project.pbxproj",
               "Classes/module/QZone/QZone/external/QZJobQueue/QZJobQueue.xcodeproj/project.pbxproj",
               "Classes/module/QZone/QZone/external/QzoneLib/QzoneLib.xcodeproj/project.pbxproj",
               "Classes/module/QZone/QZone/external/UploadSDKV2/UploadJCE/UploadJCE.xcodeproj/project.pbxproj",
               "Classes/module/QZone/QZone/external/UploadSDKV2/UploadLib.xcodeproj/project.pbxproj",
               "Classes/module/QZone/QZone.xcodeproj/project.pbxproj"]

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

def methodPattern(name):
    params = name.split(':')
    
    pattern_literal         = "@(?:(?:[\"(\[{].*[\")\]}])|\d+)"     # @"..." @(a) @[] @{} @#
    pattern_method_call     = "\[.+\]"                              # [...]
    pattern_block           = "\^.*\n*\s*\{[\s\S]*?\}"                    # ^{...}
    pattern_condition       = ".+\?.*:.+"                           # a?b:c
    pattern_selector        = "@selector\(.+\)"                     # @selector(...)
    pattern_index           = "\w+\[.+\]"                           # a[b]
    
    pattern_single_object   = "[!&+\-\*]*\w+(\+\+|--)?"             # a !a &a *a +a -a ++a a--
    pattern_convert         = "(?:\([\w *&]+\))?"+"(?:"+pattern_single_object+"|"+pattern_method_call+")"   #(type)a (type)[a selector]
    pattern_parenthesis     = "\(?"+pattern_convert+"\)?"               # (a)
    pattern_dot_syntax      = pattern_parenthesis+"(?:(\.|->)\w+)*"       # a.b a.b.c a->b (a).b (type)a.b (type)[a selector].b (type)a.b()
    pattern_cmethod_call    = pattern_dot_syntax+"(?:\(.*?\))?"           # ...()
    pattern_operator        = "(?:"+pattern_cmethod_call+"\s*[+\-*/|&]\s*)+\w+"    # a+b a|b a.b*c

#    only supports 100 named groups, pattern list should be as short as possible
    patternlist = [pattern_literal, pattern_method_call, pattern_block, pattern_condition, pattern_selector, pattern_index, pattern_cmethod_call, pattern_operator]
    pattern_all ="|".join(patternlist)
    pattern = ""
    
    pattern = ""
    #consider method like RecvMobileRequest::::::
    for i in range(0,len(params)):
        if i != len(params)-1:
            if params[i] == '':
                pattern = pattern + ":\s*(" + pattern_all + ")\s*"
            else:
                pattern = pattern + params[i] + "\s*:\s*(" + pattern_all + ")\s*"
        else:
            pattern = pattern + params[i]

    pattern = pattern + "\]"
    
    #method without parameters can be call with dot notation
    if len(params) == 1:
        pattern = pattern + "|\."+params[0]

    return pattern

def ismethodCalled(sig, pattern, content):
    selectorPattern = "@selector\("+sig+"\)"
    matchobject = re.search(selectorPattern,content)
    if not matchobject:
        matchobject = re.search(pattern,content)
    if matchobject:
        verboseprint2(bcolors.OKGREEN + matchobject.group(0) + bcolors.ENDC)
        return True
    return False

def removeCommentLine(content):
    result = re.sub(r'^\/\/.*?$','',content,flags=re.M) #multiline mode: ^...$ match one line
    result = re.sub(r'\/\*.*?\*\/','',result,flags=re.S)
    return result

def scansrc(scanheader):
    list_sourcecodes = []
    list_header = []
    #read project file
    projectfilecontent = ""
    for path in projectfilelist:
        fullpath = os.path.join(srcdir,path)
        projectfile = open(fullpath,"r")
        projectfilecontent = projectfilecontent + projectfile.read()
        projectfile.close()

    #get src file list
    filterFiles = []
    arrowExtension = [".mm",".m",".h",".cpp"]
    headerExtension = [".h"]
    for root, dirs, files in os.walk(srcdir, topdown=False):
        for name in files:
            #print(os.path.join(root, name))
            fileName, fileExtension = os.path.splitext(name)
            if not fileName in filterFiles:
                if fileExtension in arrowExtension:
                    list_sourcecodes.append(os.path.join(root, name))
                if scanheader and (fileExtension in headerExtension):
                    if " "+name+" " in projectfilecontent:
                        list_header.append(os.path.join(root,name))
                    else:
                        verboseprint2("%s not containd in project" % name)
    return list_header,list_sourcecodes

parser = argparse.ArgumentParser()
parser.add_argument("srcdir", help="specify the src directory")
parser.add_argument("--headerpath", help="specify the header file path")
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

srcdir = args.srcdir
headerpath = ""
if args.headerpath:
    headerpath = args.headerpath
    if not os.path.exists(headerpath):
        print " not exist:%s" % srcdir
        sys.exit()

if os.path.exists(srcdir):
    pass
else:
    print " not exist:%s" % srcdir
    sys.exit()

print "scanning header files and src files...."
content_sourcecodes = []
start_time = time.time()
if not len(headerpath):
    list_header, list_sourcecodes = scansrc(True)
else:
    list_header = [headerpath]
    _, list_sourcecodes = scansrc(False)

for file in list_sourcecodes:
    srcfileName = file.split("/")[-1]
    #verboseprint2(srcfileName)
    f = open(file,"r")
    fulltext = f.read()
    content = removeCommentLine(fulltext)
    f.close()
    content_sourcecodes.append((srcfileName,content))

print "done scanning %d header files and %d src files...." % (len(list_header),len(list_sourcecodes))

index = 0
count = 0

resultFile = open("notcalledmethod.txt","w")
for headerpath in list_header:
    headerfileName = headerpath.split("/")[-1]
    notCalledMethodList= []
    
    #parse header file to get method list
    methodlist = []
    f = open(headerpath,"r")
    fulltext = f.read()
    content = removeCommentLine(fulltext)
    f.close()

    methods = re.findall(r'^-\s*\([\w *&]+\)(.+?);',content,re.M)
    for methodName in methods:
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

    verboseprint1("%s : %d methods to check...." % (headerfileName, len(methodlist)))

    #parse all src file for each method
    for methodName in methodlist:
        if methodName in blacklist:
            continue
        verboseprint1("checking %s...." % methodName)
        pattern = methodPattern(methodName)
        verboseprint2(pattern)

        called = False
        for srcfileName, content in content_sourcecodes:
#            verboseprint2(srcfileName)
            called = ismethodCalled(methodName,pattern,content)
            if called:
                break;

        if not called:
            verboseprint1(bcolors.WARNING + ("find one not used method: %s" % methodName) + bcolors.ENDC)
            notCalledMethodList.append(methodName)

    if len(notCalledMethodList):
        count = count + len(notCalledMethodList)
        resultFile.write(headerfileName)
    for method in notCalledMethodList:
        resultFile.write("\t"+method+"\n")
    resultFile.flush()

    index = index + 1
    if args.verbose == None or args.verbose == 0:
        sys.stdout.write(bcolors.HEADER + ("\r%d file scaned, " % index) + "{0:.0f}% completed.       ".format((int)(float(index)/len(list_header)*100)) + bcolors.ENDC)
        sys.stdout.flush()
    else:
        print bcolors.HEADER + ("%d file scaned, " % index) + "{0:.0f}% completed.".format((int)(float(index)/len(list_header)*100)) + bcolors.ENDC

print("--- %s seconds ---" % (time.time() - start_time))
resultFile.close()

print "done! Found %d unused methods." % count
