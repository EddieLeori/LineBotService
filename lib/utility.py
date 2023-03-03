import time

def CurrentTime():
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

def CurrentDate():
    return time.strftime('%Y-%m-%d', time.localtime())

def Log(string):
    s = "[" + CurrentTime() + "] " + str(string)
    print(s)
    file = "log/log-" + CurrentDate() + ".txt"
    f = open(file, 'a')
    f.write(s + "\n")
    f.close()
