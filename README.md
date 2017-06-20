# ChaturbateRecorder

This is script to automate the recording of public webcam shows from chaturbate.com. 


I have only tested this on debian(7+8) and Mac OS X (10.10.4), but it should run on other OSs

## Requirements

Requires python3.5 or newer. You can grab python3.5.2 from https://www.python.org/downloads/release/python-352/

to install required modules, run:
```
python3.5 -m pip install livesteramer bs4 lxml
```


Edit the config file (config.conf) to point to the directory you want to record to, where your "wanted" file is located, which genders, and the interval between checks (in seconds)

Add models to the "wanted.txt" file (only one model per line). The model should match the models name in their chatrooms URL (https://chaturbate.com/{modelname}/). 
