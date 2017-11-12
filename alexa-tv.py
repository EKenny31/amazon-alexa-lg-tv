"""alexa-tv.py: Setup "devices" for your WebOS LG TV

Based of off fauxmo_minimal.py, a demo python file showing what can be done with the debounce_handler.
The handler prints True when you say "Alexa, device on" and False when you say "Alexa, device off".

If you have two or more Alexa devices, it only handles the one that hears you more clearly.
You can have an Echo per room and not worry about your handlers triggering for those other rooms.

The IP of the triggering Echo is also passed into the act() function, so you can
do different things based on which Alexa device triggered the handler.

Tips:
- Run "python lgtv.py listInputs" to find app IDs
- See lgtv.py for other available functionality
"""
import fauxmo
import logging
import debounce_handler
import subprocess

# Logging
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG, datefmt='%H:%M:%S')

# TV Configuration
DEFAULT_VOLUME = 15
DEVICE_START_PORT = 52000  # TODO: Why 52000?
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


def lgtv_call(command, before_msg=None, after_msg=None, popen=False):
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
        logging.info(before_msg)

    args = ['python', 'lgtv.py'] + command.split()
    if popen:  # Don't wait for the process to return
        subprocess.Popen(args)
    else:
        subprocess.call(args)

    if after_msg:
        logging.info(after_msg)

    return True


class device_handler(debounce_handler.debounce_handler):
    """Publishes the on/off state requested and the IP address of the Echo making the request."""
    custom_triggers = APPS.keys() + INPUTS.keys()
    triggers = {name: DEVICE_START_PORT+i for i, name in enumerate(DEFAULT_TRIGGERS + custom_triggers)}

    def act(self, client_address, state, name):
        """Given a request, execute the desired action.

        Voice commands are in the format "Alexa, turn <name> [on, off]"

        Arguments:
            client_address (str): IP address of the Alexa device that received the voice command
            state (bool):         Desired state, either on or off
            name (str):           Name of the device to perform the action on, aka trigger name

        Returns:
            True if success.
        """
        logging.debug('Name: {}, State: {}, Client {}'.format(name, state, client_address))

        # TV On/Off
        if name == 'tv' and state is True:
            lgtv_call('on', 'Turning on...', 'Turned on!', popen=True)
        elif name == 'tv' and state is False:
            lgtv_call('off', 'Turning off...', 'Turned off!', popen=True)

        # Volume
        elif name == 'volume' and state is True:
            lgtv_call('setVolume {}'.format(DEFAULT_VOLUME), 'Volume set to {}'.format(DEFAULT_VOLUME))
        elif name == 'volume' and state is False:
            lgtv_call('setVolume 0', 'Volume set to 0')
        elif name == 'up':
            lgtv_call('volumeUp', 'Volume up')
        elif name == 'down':
            lgtv_call('volumeDown', 'Volume down')
        elif name == 'mute' and state is True:
            lgtv_call('mute muted', 'Muted')
        elif name == 'mute' and state is False:
            # Volume up is the only I way I know how to unmute
            lgtv_call('volumeUp')
            lgtv_call('volumeDown', 'Unmuted')  # Volume down to maintain same volume level

        # Playback
        elif name == 'playback' and state is True:
            lgtv_call('inputMediaPlay', 'Playback set to RESUME')
        elif name == 'playback' and state is False:
            lgtv_call('inputMediaPause', 'Playback set to PAUSE')

        # Inputs
        elif name in INPUTS.keys():
            lgtv_call('setInput {}'.format(INPUTS[name]), 'Input set to {}'.format(name))

        # Apps
        elif name in APPS.keys():
            if state is True:
                lgtv_call('startApp {}'.format(APPS[name]), 'Started {}'.format(name))
            else:
                lgtv_call('closeApp {}'.format(APPS[name]), 'Closed {}'.format(name))

        return True


if __name__ == '__main__':
    # Startup the fauxmo server
    fauxmo.DEBUG = True
    poller = fauxmo.poller()
    listener = fauxmo.upnp_broadcast_responder()
    listener.init_socket()
    poller.add(listener)

    # Register the device callback as a fauxmo handler
    device_handler = device_handler()
    for trigger, port in device_handler.triggers.items():
        fauxmo.fauxmo(trigger, listener, poller, None, port, device_handler)

    # Loop and poll for incoming Alexa device requests
    logging.debug('Entering fauxmo polling loop')
    while True:
        try:
            poller.poll(100)
        except Exception, e:
            logging.critical('Critical exception: ' + str(e))
            break
