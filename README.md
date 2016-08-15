脚本可用于扫描iOS工程中未被调用到的方法，使用方法如下：

1.将以下文件放到脚本所在目录下：
 a.arm64和armv7两个linkmap文件
 b.QQ for iOS安装包（ipa文件）

2.运行脚本：
python unused_selector_otool.py

3.结果放在result.txt中，静态库中的未调用方法放在staticlibresult.txt中
