import time, datetime, os, sys, requests, configparser, re, subprocess
from queue import Queue
from livestreamer import Livestreamer
from threading import Thread
from bs4 import BeautifulSoup

Config = configparser.ConfigParser()
Config.read(sys.path[0] + "/config.conf")
save_directory = Config.get('paths', 'save_directory')
wishlist = Config.get('paths', 'wishlist')
interval = int(Config.get('settings', 'checkInterval'))
genders = re.sub(' ', '', Config.get('settings', 'genders')).split(",")
directory_structure = Config.get('paths', 'directory_structure').lower()
postProcessingCommand = Config.get('settings', 'postProcessingCommand')
try:
    postProcessingThreads = int(Config.get('settings', 'postProcessingThreads'))
except ValueError:
    pass
completed_directory = Config.get('paths', 'completed_directory').lower()


recording = []

def startRecording(model):
    global postProcessingCommand
    global processingQueue
    try:
        gender = ""
        URL = "https://chaturbate.com/{}/".format(model)
        result = requests.get(URL, headers={'Connection':'close'})
        result = result.text
        for line in result.splitlines():
            if "m3u8" in line:
                stream = line.split("'")[1]
                break
        soup = BeautifulSoup(result, 'lxml')
        soup = soup.find('div', {'id': "tabs_content_container"})
        soup = soup.find('dl')
        for line in str(soup).splitlines():
            if "<dt>Sex:</dt>" in line:
                gender = re.sub("<dt>Sex:</dt><dd>", "", line)[:-5]
                break
        session = Livestreamer()
        session.set_option('http-headers', "referer=https://www.chaturbate.com/{}".format(model))
        streams = session.streams("hlsvariant://{}".format(stream))
        stream = streams["best"]
        fd = stream.open()
        now = datetime.datetime.now()
        filePath = directory_structure.format(path=save_directory, model=model, gender=gender,
                                              seconds=now.strftime("%S"),
                                              minutes=now.strftime("%M"), hour=now.strftime("%H"),
                                              day=now.strftime("%d"),
                                              month=now.strftime("%m"), year=now.strftime("%Y"))
        directory = filePath.rsplit('/', 1)[0]+'/'
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(filePath, 'wb') as f:
            recording.append(model)
            while True:
                try:
                    data = fd.read(1024)
                    f.write(data)
                except:
                    f.close()
                    recording.remove(model)
                    if postProcessingCommand != "":
                        processingQueue.put({'model':model, 'path':filePath, 'gender':gender})
                    elif completed_directory != "":
                        finishedDir = completed_directory.format(path=save_directory, model=model,
                                                                 gender=gender, seconds=now.strftime("%S"),
                                                                 minutes=now.strftime("%M"),
                                                                 hour=now.strftime("%H"), day=now.strftime("%d"),
                                                                 month=now.strftime("%m"), year=now.strftime("%Y"))

                        if not os.path.exists(finishedDir):
                            os.makedirs(finishedDir)
                        os.rename(filePath, finishedDir+'/'+filePath.rsplit['/',1][0])
                    return

        if model in recording:
            recording.remove(model)
    except:
        if model in recording:
            recording.remove(model)
def postProcess():
    global processingQueue
    global postProcessingCommand
    while True:
        while processingQueue.empty():
            time.sleep(1)
        parameters = processingQueue.get()
        model = parameters['model']
        path = parameters['path']
        filename = path.rsplit('/', 1)[1]
        gender = parameters['gender']
        directory = path.rsplit('/', 1)[0]+'/'
        subprocess.run(postProcessingCommand.split() + [path, filename, directory, model, gender])


if __name__ == '__main__':
    AllowedGenders = ['female', 'male', 'trans', 'couple']
    genders = [a.lower() for a in genders]
    for gender in genders:
        if gender.lower() not in AllowedGenders:
            print(gender, "is not an acceptable gender, options are: female, male, trans, and couple - please correct your config file")
            exit()
    print()
    if postProcessingCommand != "":
        processingQueue = Queue()
        postprocessingWorkers = []
        for i in range(0, postProcessingThreads):
            t = Thread(target=postProcess)
            postprocessingWorkers.append(t)
            t.start()
    sys.stdout.write("\033[F")
    while True:
        sys.stdout.write("\033[K")
        print("{} model(s) are being recorded. Getting list of online models now".format(len(recording)))
        sys.stdout.write("\033[K")
        print("the following models are being recorded: {}".format(recording), end="\r")
        online = subprocess.check_output([sys.executable, sys.path[0] + "/getModels.py"])
        online = online.decode('utf-8').splitlines()
        f = open(wishlist, 'r')
        for theModel in list(set(f.readlines())):
            theModel = list(filter(None, theModel.split('chaturbate.com/')))[-1].lower().strip().replace('/', '')
            if theModel in online\
                    and theModel not in recording:
                thread = Thread(target=startRecording, args=(theModel,))
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
