# Amazon Alexa LG TV

Use your Echo or Echo Dot to turn on/off your LG TV.

You need a TV with WebOS 2.0+.

## Usage

- "Alexa, turn on TV"
- "Alexa, turn off the TV"
- "Alexa, turn on Netflix"
- "Alexa, turn off Netflix"
- "Alexa, turn on HDMI1"
- "Alexa, turn on Volume" (unmute)
- "Alexa, turn off the Volume" (mute)
- "Alexa, turn on mute"
- "Alexa, turn off mute"
- "Alexa, turn on X" (sets volume to X)
- "Alexa, turn on CX" (increases volume by X)
- "Alexa, turn off CX" (decreases volume by X)
- "Alexa, turn on Playback" (Can also be used as an "OK" button when on a Netflix "Are you still watching?" prompt.)
- "Alexa, turn off Playback"

(You can also use stop/start in place of the turn on/off invocation)

## Customize Commands
- If you want to add an app trigger, add it to the APPS dictionary. They keys are trigger names and the values are app IDS. You can find the app names by calling "python lgtv.py listApps"

- If you want to add a new input trigger, add it to the INPUTS dictionary. The keys are trigger names and the values are input names (e.g. 'HDMI_1')


See https://github.com/klattimer/LGWebOSRemote for a full list of commands.

## Install

- Clone this repository
- Install python (I used 2.7.14 and recommend using pyenv—you will need to make some changes if you want to use Python 3)
- Run "pip install -r requirements.txt"
- Authenticate with "python lgtv.py auth [IP Address]"
- Start the script with `python alexa-tv.py`
- Enable "Mobile TV On" in your TV settings (should be under "General")
- On the Alexa App, go to "Smart Home" > "Devices" > "Discover" for Alexa to discover the new devices

When you try to turn on/off the TV for the first you will need to allow the script to access your TV. Alternatively, run "python lgtv.py auth [IP Address]"

### Supervisord

You can use supervisord to run your script
Sample config:

```
[program:alexa-tv]
command=/usr/bin/python /srv/amazon-alexa-lg-tv/alexa-tv.py
process_name=%(program_name)s
numprocs=1
directory=/srv/amazon-alexa-lg-tv/
autorestart=true
user=nobody                   ; setuid to this UNIX account to run the program
redirect_stderr=true
stdout_logfile=/var/log/alexa-tv.log
stdout_logfile_maxbytes=1MB
stdout_capture_maxbytes=1MB
```

## Thanks

- https://github.com/toddmedema/echo
- https://github.com/klattimer/LGWebOSRemote
- https://github.com/akhan23wgu/amazon-alexa-lg-tv
