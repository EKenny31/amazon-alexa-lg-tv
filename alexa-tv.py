"""alexa-tv.py: Setup "devices" for your WebOS LG TV

Based of off fauxmo_minimal.py, a demo python file showing what can be done with the debounce_handler.
The handler prints True when you say "Alexa, device on" and False when you say "Alexa, device off".

If you have two or more Echos, it only handles the one that hears you more clearly.
You can have an Echo per room and not worry about your handlers triggering for those other rooms.

The IP of the triggering Echo is also passed into the act() function, so you can
do different things based on which Alexa device triggered the handler.
"""
import fauxmo
import logging
import os
from debounce_handler import debounce_handler
import subprocess

# TODO: Look at this
logging.basicConfig(level=logging.DEBUG)

# Configuration
DEFAULT_VOLUME = 15
DEVICE_START_PORT = 52000  # TODO: Any reason why 52000 in particular?
DEFAULT_TRIGGERS = ['tv', 'volume', 'up', 'down', 'mute', 'playback']
APPS = {  # Dictionary of trigger name to app ID
    'netflix': 'netflix',
    'youtube': 'youtube.leanback.v4',
    'amazon': 'amazon',
    'gallery': 'com.webos.app.igallery',
}
INPUTS = {  # Dictionary of trigger name to input
    'chromecast': 'HDMI_1',
    'playstation': 'HDMI_2',
    'pc': 'HDMI_3',
}


def call(command, before_msg=None, after_msg=None, popen=False):
    """Run specified LGWebOSRemote command using subprocess.call.

    Arguments:
        command (str):       command to run in the format 'python lgtv.py <command>'
        before_msg (str):    message to print before command is run
        after_msg (str):     message to print after command is run
        popen (bool):        whether to use subprocess.Popen instead of subprocess.call

    Returns:
        True if success
    """
    if before_msg:
        print before_msg

    args = ['python', 'lgtv.py'] + command.split()
    if popen:  # Don't wait for the process to return
        subprocess.Popen(args)
    else:
        subprocess.call(args)

    if after_msg:
        print after_msg

    return True


class device_handler(debounce_handler):
    """Publishes the on/off state requested and the IP address of the Echo making the request."""
    CUSTOM_TRIGGERS = APPS.keys() + INPUTS.keys()
    TRIGGERS = {name: DEVICE_START_PORT+i for i, name in enumerate(DEFAULT_TRIGGERS + CUSTOM_TRIGGERS)}

    def act(self, client_address, state, name):
        print 'Name: {}, State: {}, Client {}'.format(name, state, client_address)

        # TV On/Off
        if name == 'tv' and state is True:
            call('on', 'Turning on...', 'Turned on!', popen=True)
        elif name == 'tv' and state is False:
            call('off', 'Turning off...', 'Turned off!', popen=True)

        # Volume
        elif name == 'volume' and state is True:
            call('setVolume {}'.format(DEFAULT_VOLUME), 'Volume set to {}'.format(DEFAULT_VOLUME))
        elif name == 'volume' and state is False:
            call('setVolume 0', 'Volume set to 0')
        elif name == 'up':
            call('volumeUp', 'Volume up')
        elif name == 'down':
            call('volumeDown', 'Volume down')
        elif name == 'mute' and state is True:
            call('mute muted', 'Muted')
        elif name == 'mute' and state is False:
            # Volume up is the only I way I know how to unmute
            call('volumeUp')
            call('volumeDown', 'Unmuted')  # Volume down to maintain same volume level

        # Playback
        elif name == 'playback' and state is True:
            call('inputMediaPlay', 'Playback set to RESUME')
        elif name == 'playback' and state is False:
            call('inputMediaPause', 'Playback set to PAUSE')

        # Inputs
        elif name in INPUTS.keys():
            call('setInput {}'.format(INPUTS[name]), 'Input set to {}'.format(name))

        # Apps
        elif name in APPS.keys():
            if state is True:
                call('startApp {}'.format(APPS[name]), 'Started {}'.format(name))
            else:
                call('closeApp {}'.format(APPS[name]), 'Closed {}'.format(name))

        return True


if __name__ == '__main__':
    # Startup the fauxmo server
    fauxmo.DEBUG = True
    p = fauxmo.poller()
    u = fauxmo.upnp_broadcast_responder()
    u.init_socket()
    p.add(u)

    # Register the device callback as a fauxmo handler
    d = device_handler()
    for trig, port in d.TRIGGERS.items():
        fauxmo.fauxmo(trig, u, p, None, port, d)

    # Loop and poll for incoming Echo requests
    logging.debug('Entering fauxmo polling loop')
    while True:
        try:
            p.poll(100)
        except Exception, e:
            logging.critical('Critical exception: ' + str(e))
            break
