import time, datetime, os, sys, requests, configparser, re, subprocess
from livestreamer import Livestreamer
from threading import Thread
from bs4 import BeautifulSoup

Config = configparser.ConfigParser()
Config.read(sys.path[0] + "/config.conf")
save_directory = Config.get('paths', 'save_directory')
wishlist = Config.get('paths', 'wishlist')
interval = int(Config.get('settings', 'checkInterval'))
genders = re.sub(' ', '', Config.get('settings', 'genders')).split(",")
lastPage = {'female': 100, 'couple': 100, 'trans': 100, 'male': 100}
directory_structure = Config.get('paths', 'directory_structure').lower()


recording = []

def startRecording(model):
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
        if not os.path.exists(
                directory_structure.format(path=save_directory, model=model, gender=gender, seconds=now.strftime("%S"),
                                           minutes=now.strftime("%M"), hour=now.strftime("%H"), day=now.strftime("%d"),
                                           month=now.strftime("%m"), year=now.strftime("%Y")).rsplit('/', 1)[0]):
            os.makedirs(directory_structure.format(path=save_directory, model=model, gender=gender, seconds=now.strftime("%S"),
                                           minutes=now.strftime("%M"), hour=now.strftime("%H"), day=now.strftime("%d"),
                                           month=now.strftime("%m"), year=now.strftime("%Y")).rsplit('/', 1)[0])
        with open(directory_structure.format(path=save_directory, model=model, gender=gender, seconds=now.strftime("%S"),
                                           minutes=now.strftime("%M"), hour=now.strftime("%H"), day=now.strftime("%d"),
                                           month=now.strftime("%m"), year=now.strftime("%Y")), 'wb') as f:
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
    print()
    sys.stdout.write("\033[F")
    while True:
        sys.stdout.write("\033[K")
        print("{} model(s) are being recorded. Getting list of online models now".format(len(recording)))
        sys.stdout.write("\033[K")
        print("the following models are being recorded: {}".format(recording), end="\r")
        lastPage = {'female': 100, 'couple': 100, 'trans': 100, 'male': 100}
        online = subprocess.check_output([sys.executable, sys.path[0] + "/getModels.py"])
        f = open(wishlist, 'r')
        for theModel in f.readlines():
            theModel = list(filter(None, theModel.split('/')))[-1]
            if bytes(theModel.lower(), 'utf-8') in online\
                    and theModel.lower().strip() not in recording:
                thread = Thread(target=startRecording, args=(theModel.lower().strip(),))
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

