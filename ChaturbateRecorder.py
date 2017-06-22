import urllib.request, time, datetime, os, threading, sys, requests, configparser, re, gevent
from bs4 import BeautifulSoup
from livestreamer import Livestreamer
from threading import Thread
from queue import Queue

Config = configparser.ConfigParser()
Config.read(sys.path[0] + "/config.conf")
save_directory = Config.get('paths', 'save_directory')
wishlist = Config.get('paths', 'wishlist')
interval = int(Config.get('settings', 'checkInterval'))
genders = re.sub(' ', '', Config.get('settings', 'genders')).split(",")
lastPage = {'female': 100, 'couple': 100, 'trans': 100, 'male': 100}

online = []
q = Queue()
online = []

class checkForModels:
    global q
    global online
    def getModels(self):
        workers = []
        for gender in genders:
            if gender is 'couple':
                for i in range(1, 3):
                    q.put([i, gender])
            else:
                for i in range(1, 30):
                    q.put([i, gender])
        while not q.empty():
            for i in range(10):
                t = Thread(target=getOnlineModels)
                workers.append(t)
                t.start()
            for t in workers:
                t.join()


recording = []
def getOnlineModels():
    global lastPage
    global q
    global online
    if not q.empty():
        args = q.get()
        page = args[0]
        gender = args[1]
        if page < lastPage[gender]:
            attempt = 1
            while attempt <= 3:
                try:
                    timeout = gevent.Timeout(8)
                    timeout.start()
                    URL = "https://chaturbate.com/{gender}-cams/?page={page}".format(gender=gender.lower(), page=page)
                    result = requests.request('GET', URL)
                    result = result.text
                    soup = BeautifulSoup(result, 'lxml')
                    if lastPage[gender] == 100:
                        lastPage[gender] = int(soup.findAll('a', {'class': 'endless_page_link'})[-2].string)
                    if int(soup.findAll('li', {'class': 'active'})[1].string) == page:
                        LIST = soup.findAll('ul', {'class': 'list'})[0]
                        models = LIST.find_all('div', {'class': 'title'})
                        for model in models:
                            online.append(model.find_all('a', href=True)[0].string.lower()[1:])
                    break
                except gevent.Timeout:
                    attempt = attempt + 1
                    if attempt > 3:
                        break


def startRecording(model):
    try:
        URL = "https://chaturbate.com/{}/".format(model)
        result = urllib.request.urlopen(URL)
        result = result.read().decode()
        for line in result.splitlines():
            if "m3u8" in line:
                stream = line.split("'")[1]
                break
        session = Livestreamer()
        session.set_option('http-headers', "referer=https://www.chaturbate.com/{}".format(model))
        streams = session.streams("hlsvariant://{}"
          .format(stream))
        stream = streams["best"]
        fd = stream.open()
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime("%Y.%m.%d_%H.%M.%S")
        if not os.path.exists("{path}/{model}".format(path=save_directory, model=model)):
            os.makedirs("{path}/{model}".format(path=save_directory, model=model))
        with open("{path}/{model}/{st}_{model}.mp4".format(path=save_directory, model=model,
                                                           st=st), 'wb') as f:
            recording.append(model)
            while True:
                try:
                    data = fd.read(1024)
                    f.write(data)
                except:
                    f.close()
                    recording.remove(model)
                    return

        if model in recording:
            recording.remove(model)
    except:
        if model in recording:
            recording.remove(model)


if __name__ == '__main__':
    AllowedGenders = ['female', 'male', 'trans', 'couple']
    genders = [a.lower() for a in genders]
    for gender in genders:
        if gender.lower() not in AllowedGenders:
            print(gender, "is not an acceptable gender, options are: female, male, trans, and couple - please correct your config file")
            exit()
    checker = checkForModels()
    print()
    sys.stdout.write("\033[F")
    while True:
        sys.stdout.write("\033[K")
        print("{} model(s) are being recorded. Getting list of online models now".format(len(recording)))
        sys.stdout.write("\033[K")
        print("the following models are being recorded: {}".format(recording), end="\r")
        lastPage = {'female': 100, 'couple': 100, 'trans': 100, 'male': 100}
        online = []
        checker.getModels()
        online = list(set(online))
        with open(wishlist) as f:
            for model in f:
                models = model.split()
                for theModel in models:
                    if theModel.lower() in online and theModel.lower() not in recording:
                        thread = threading.Thread(target=startRecording, args=(theModel.lower(),))
                        thread.start()
        f.close()
        sys.stdout.write("\033[F")
        for i in range(interval, 0, -1):
            sys.stdout.write("\033[K")
            print("{} model(s) are being recorded. Next check in {} seconds".format(len(recording), i))
            sys.stdout.write("\033[K")
            print("the following models are being recorded: {}".format(recording), end="\r")
            time.sleep(1)
            sys.stdout.write("\033[F")
