from __future__ import division
import threading
import time
import os
from subprocess import Popen
from livestreamer import Livestreamer
import random
import ConfigParser
import datetime

path = os.path.dirname(__file__)


class Channel(threading.Thread):
    quality = 'high'
    wait = 10
    warningLevel = 1

    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID

    def run(self):
        threadID = self.threadID
        warned = 0
        warnedQuality = 0
        giveMeAChance = 1  #if a stream is available let channel give an warning
        sleep = 0
        streaming = 0
        startStream = 0
        end_after_done = 0

        time.sleep(5.00 * float(threadID) / float(ChannelParser.currentSize))
        config = ChannelParser.config
        reason = ''
        print 'added: Section ' + str(threadID) + ', channel ' + config.get(str(threadID), 'channel')
        while True:
            if MainClass.die:  #do main() want you dead?
                reason = 'die == true'
                break
            if not config.has_section(str(threadID)):  #is section still in config
                reason = 'config.has_section == False'
                break
            channel = config.get(str(threadID), 'channel')
            warningLevel = int(config.get(str(threadID), 'warning level'))
            wait = int(config.get(str(threadID), 'wait'))
            quality = config.get(str(threadID), 'quality')
            if ChannelParser.startStream == str(threadID):
                startStream = 1
                giveMeAChance = 1
                sleep = 0
                ChannelParser.startStream = -1
            if ChannelParser.endStream == str(threadID):
                startStream = 0
                ChannelParser.endStream = -1
                if (warningLevel == 2):
                    sleep += 21600
            if ChannelParser.sleep:  #do main() want all channels to sleep
                sleep += 2.00
            if sleep >= 2.00:  #do needed sleep
                time.sleep(2.25 + random.uniform(-0.25, 0.25))
                sleep -= 2.00
                if startStream == 1:
                    if end_after_done >= 1000:
                        startStream = 0
                        end_after_done = 0
                    else:
                        end_after_done += 1
                elif startStream == 0 and not end_after_done == 0:
                    end_after_done = 0
                continue
            if not warningLevel > 1 and not startStream:
                if not warningLevel:
                    if not giveMeAChance:
                        if streaming:
                            giveMeAChance = 1
                            sleep += 100.00
                        continue
            try:  # check for available stream
                livestreamer = Livestreamer()
                plugin = livestreamer.resolve_url(channel)
                plugin = plugin.get_streams()
                keys = plugin.keys()
            except:  #another channel was using plugin causing error, to lazy to make a real lock function
                time.sleep(random.uniform(0.0, 2.0))
                if ChannelParser.printLevel == 1:
                    print 'plugin error: ' + str(threadID) + ', ' + channel
                continue
            if ChannelParser.printLevel == 1:
                print 'checked: ' + str(threadID) + ', ' + channel
            if not keys:  #check if stream is available
                if threadID in ChannelParser.streaming:
                    if warnedQuality and not streaming:
                        warnedQuality = 0
                    ChannelParser.streaming.remove(threadID)
                if streaming:
                    st = datetime.datetime.now().strftime('%H:%M')
                    print '[' + st + '] stream ended: ' + str(threadID) + ', ' + channel
                    giveMeAChance = 1
                streaming = 0
                warned = 0
                sleep += (wait * 10 + 6.00)
                continue
            else:
                streaming = 1

            if quality in keys:  #start or ignore stream
                if not threadID in ChannelParser.streaming:
                    ChannelParser.streaming.append(threadID)
                warnedQuality = 0
                if warningLevel > 1 or startStream:
                    args = channel + ' ', quality
                    st = datetime.datetime.now().strftime('%H:%M')
                    print '[' + st + '] starting stream: ' + str(threadID) + ', ' + channel
                    livestreamerProcess = Popen(['livestreamer.exe', args])
                    livestreamerProcess.wait()
                    st = datetime.datetime.now().strftime('%H:%M')
                    print '[' + st + '] ending stream: ' + str(threadID) + ', ' + channel
                    sleep += 10.00
                    continue
                elif warningLevel:
                    if not warned:
                        st = datetime.datetime.now().strftime('%H:%M')
                        print '[' + st + '] stream started: ' + str(threadID) + ', ' + channel + '\a'
                        warned = 1
                        sleep += 10
                    else:
                        sleep += wait * 10 + 6.00
                else:
                    if not warned:
                        warned = 1
                        st = datetime.datetime.now().strftime('%H:%M')
                        print '[' + st + '] ignored: ' + str(threadID) + ', ' + channel
                    giveMeAChance = 0  #have been given one
                    continue
            else:  #quality not in list, show alternatives
                if warningLevel:
                    if not warnedQuality:
                        warnedQuality = 1
                        print 'warning: ' + str(
                            threadID) + ', ' + channel + ' does not support ' + quality + '\n' + 'supported formats: ' + ','.join(
                            keys)
                        sleep += 10
                    continue
                else:
                    sleep += wait * 10 + 2.00
        print 'thread ' + str(threadID) + ' ended: from ' + reason


class ChannelParser:
    newThreads = []
    currentSize = 0
    sleep = 0
    config = ConfigParser.RawConfigParser()
    nextSection = 0
    startStream = -1
    endStream = -1
    streaming = []
    printLevel = 0


    @staticmethod
    def updateCurrentSize():
        config = ChannelParser.config
        i = -1
        j = 0
        while True:
            if j >= 10:
                break
            if config.has_section(str(i)):
                i += 1
                j = 0
            else:
                i += 1
                j += 1
        return i - 10

    @staticmethod
    def updateNextSection():
        config = ChannelParser.config
        i = 0
        while True:
            if config.has_section(str(i)):
                i += 1
            else:
                return i

    @staticmethod
    def updateVars():  #load channels from file
        ChannelParser.config.read('channels.ini')
        ChannelParser.currentSize = ChannelParser.updateCurrentSize()
        ChannelParser.nextSection = ChannelParser.updateNextSection()

    @staticmethod
    def writeVar(section, var, value):
        config = ChannelParser.config
        config.set(section, var, value)
        with open('channels.ini', 'wb') as configfile:
            config.write(configfile)

    @staticmethod
    def writeChannelSection(section, values):
        config = ChannelParser.config
        config.add_section(section)
        config.set(section, 'channel', values[0])
        if len(values) > 3:
            config.set(section, 'wait', values[1])
            config.set(section, 'quality', values[2])
            config.set(section, 'warning level', values[3])
        else:
            config.set(section, 'wait', config.get('defaults', 'wait'))
            config.set(section, 'quality', config.get('defaults', 'quality'))
            config.set(section, 'warning level', config.get('defaults', 'warning level'))
        ChannelParser.newThreads.append(section)
        with open('channels.ini', 'wb') as configfile:
            config.write(configfile)

    @staticmethod
    def removeSection(section):
        config = ChannelParser.config
        if config.has_section(section):
            config.remove_section(section)
            with open('channels.ini', 'wb') as configfile:
                config.write(configfile)
        else:
            print 'config does not contain: ' + str(section)

    @staticmethod
    def list():
        config = ChannelParser.config
        for i in range(0, ChannelParser.currentSize + 1):
            if config.has_section(str(i)):
                print 'Section ' + str(i) + ', channel ' + config.get(str(i), 'channel')

    @staticmethod
    def listAll():
        config = ChannelParser.config
        print 'Section | Enabled | Wait | Quality | Channel'
        for i in range(0, ChannelParser.currentSize + 1):
            if config.has_section(str(i)):
                print '    ' + str(i) + '    |    ' + config.get(str(i), 'warning level') + '   |   ' + config.get(
                    str(i), 'wait') + '   |   ' + config.get(str(i), 'quality') + '   |   ' + config.get(str(i),
                                                                                                         'channel')

    @staticmethod
    def listStreams():
        config = ChannelParser.config
        print 'currently streaming:'
        for i in ChannelParser.streaming:
            if config.has_section(str(i)):
                print 'Section ' + str(i) + ', ' + config.get(str(i), 'channel')

    @staticmethod
    def toString():
        print 'currentSize: ' + str(ChannelParser.currentSize)
        print 'sleep: ' + str(ChannelParser.sleep)
        print 'nextSection: ' + str(ChannelParser.nextSection)


class MainClass:
    die = 0

    @staticmethod
    def run():

        config = ChannelParser.config
        newThreads = ChannelParser.newThreads
        ChannelParser.updateVars()
        ChannelParser.toString()
        threads = []
        IOThread = BasicIO(0)
        IOThread.start()
        for i in range(0, ChannelParser.currentSize):  #new threads for all sections
            if config.has_section(str(i)):
                tempThread = Channel(i)
                tempThread.start()
                threads.append(tempThread)
        i = 0
        try:  #keep main() running, updating channel threads and creating new threads
            while not MainClass.die:
                time.sleep(2)
#                ChannelParser.updateVars()
                while newThreads:  # while there are sections that not have threads
                    i = newThreads.pop(0)
                    tempThread = Channel(i)
                    tempThread.start()
                    threads.append(tempThread)
        except:  #kill threads
            MainClass.die = 1
            raise


class BasicIO(threading.Thread):
    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID

    def run(self):
        while not MainClass.die:
            line = raw_input('')
            if not line:
                continue
            line = line.split()
            wordOne = line[0]
            rest = line[1:]
            if wordOne == 'start' or wordOne == 'enable':
                if len(line) > 1:
                    ChannelParser.startStream = line[1]
                else:
                    print 'argument?'
            elif wordOne == 'end' or wordOne == 'disable':
                if len(line) > 1:
                    ChannelParser.endStream = line[1]
                else:
                    print 'argument?'
            elif wordOne == 'add':
                ChannelParser.updateVars()
                ChannelParser.writeChannelSection(str(ChannelParser.nextSection), rest)
            elif wordOne == 'list':
                if rest:
                    if rest[0] == 'streams':
                        ChannelParser.listStreams()
                    else:
                        ChannelParser.listAll()
                else:
                    ChannelParser.list()
            elif wordOne == 'remove':
                if len(line) > 1:
                    ChannelParser.removeSection(line[1])
            elif wordOne == 'change':
                if len(line) > 3 and line[2] in ['wait', 'quality', 'warning', 'channel']:
                    if line[2] == 'warning':
                        line[2] = 'warning level'
                    ChannelParser.writeVar(line[1], line[2], line[3])
                else:
                    print 'argument?'
            elif wordOne == 'die' or wordOne == 'q':
                MainClass.die = 1
            elif wordOne == 'sleep':
                ChannelParser.sleep = not ChannelParser.sleep
            elif wordOne == 'print':
                if rest:
                    ChannelParser.printLevel = int(rest[0])
            elif wordOne == 'help':
                print '\n'
                print '  start/enable $section  |  yay'
                print '  end/disable $section  |  zzzz'
                print '  add $channel/$channel $wait $quality $warningLevel  |  add channel with default or args'
                print '  list/list all/list streams  |  list channels/list everything in config/list currently streaming'
                print '  remove $section  |  removes section from config'
                print '  change $section $var $value  |  change value | $var - wait, quality, warning, channel'
                print '  die/q  |  kill everything nicely'
                print '  sleep  |  nothing happens'
                print '  print $level  |  level 1 for listing when channels are checked'
            else:
                print 'try again'


def main():
    MainClass().run()


if __name__ == "__main__":
    main()

