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
import json
import time

# Logging
LOG_LEVEL = logging.INFO
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=LOG_LEVEL, datefmt='%H:%M:%S')

# TV Configuration
MAX_VOLUME = 100
DEFAULT_TRIGGERS = ['tv', 'volume', 'mute', 'playback']
SET_VOLUME_CONTROLS = range(0, MAX_VOLUME+1)  # Range of values you can set the volume to
CHANGE_VOLUME_CONTROLS = range(1, 11)  # Values you can change the volume by
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
    current_volume = None
    muted = None
    change_volume_controls = None
    set_volume_controls = None
    triggers = {}
    set_volume_controls = map(str, SET_VOLUME_CONTROLS)
    change_volume_controls = map(lambda x: 'c{}'.format(x), CHANGE_VOLUME_CONTROLS)

    # Define starting port for triggers
    # Give each category of triggers its own range to prevent interference when adding new triggers
    DEFAULT_TRIGGERS_START_PORT = 52000
    APPS_START_PORT = 53000
    INPUTS_START_PORT = 54000
    SET_VOLUME_START_PORT = 55000
    CHANGE_VOLUME_START_PORT = 56000

    def add_triggers(self, trigger_names, start_port=None):
        """Add specified trigger names to internal dictionary of trigger names to ports.

        Arguments:
            trigger_names (list): list of trigger names to add
            start_port (int):     start of the desired port range, not required for set/change volume triggers
        """
        for i, trigger_name in enumerate(trigger_names):
            # If volume control, determine port based on integer in trigger_name
            # This prevents inteference when changing the ranges/registering new triggers
            if trigger_name in self.set_volume_controls:
                self.triggers[trigger_name] = self.SET_VOLUME_START_PORT + int(trigger_name)
            elif trigger_name in self.change_volume_controls:
                self.triggers[trigger_name] = self.CHANGE_VOLUME_START_PORT + int(trigger_name.lstrip('c'))
            else:  # Otherwise, use specified port
                self.triggers[trigger_name] = start_port + i

    def init_triggers(self):
        """Initialize triggers based on configuration."""
        self.add_triggers(DEFAULT_TRIGGERS, self.DEFAULT_TRIGGERS_START_PORT)
        self.add_triggers(APPS.keys(), self.APPS_START_PORT)
        self.add_triggers(INPUTS.keys(), self.INPUTS_START_PORT)

        # Only add volume controls if volume is a default trigger
        if 'volume' in DEFAULT_TRIGGERS:
            self.add_triggers(self.set_volume_controls)
            self.add_triggers(self.change_volume_controls)

        logging.info('Triggers: {}'.format(self.triggers))

    def check_volume_status(self):
        """Check and current volume/whether muted and update internal status.

        Returns:
            True if success, False if bad response
        """
        # Use Popen to get the response
        pipe = subprocess.PIPE
        process = subprocess.Popen(['python', 'lgtv.py', 'audioVolume'], stdin=pipe, stdout=pipe, stderr=pipe)
        output, error = process.communicate()
        # TODO: Add try, except for this
        response, closing = output.rstrip('\n').split('\n')  # Except two responses separated by newline with trailing newline

        # Load response
        try:
            response_json = json.loads(response)
        except Exception as e:
            logging.error('volumeStatus response is not JSON: {}'.format(response))
            logging.error('json.loads exception: {}'.format(e))
            return False
        try:
            payload = response_json['payload']
            self.current_volume = payload['volume']
            self.muted = payload['muted']
        except Exception as e:
            logging.error('bad volumeStatus response: {}'.format(e))
            return False

        logging.debug('Current volume: {}'.format(self.current_volume))
        logging.debug('Muted: {}'.format(self.muted))
        return True

    # TODO: Use state to decide whether to turn on/off mute?
    # Currently, mute will stay on when setting/changing volume
    def set_volume(self, name):
        """Set volume to specified level.

        Arguments:
            name (str): trigger name, expected to be an integer in string format
        """
        volume_to_set = int(name)
        if volume_to_set == self.current_volume:
            logging.info('Volume is already {}'.format(self.current_volume))
        else:
            lgtv_call('setVolume {}'.format(volume_to_set), 'Volume set to {}'.format(volume_to_set))

    def change_volume(self, name, state):
        """Increase/decrease volume by the specified amount.

        Arguments:
            name (str):   trigger name with expected format c<delta>, where delta is an integer in string format
            state (bool): whether to increase or decrease volume
        """
        delta = int(name.lstrip('c'))
        volume_to_set = self.current_volume + delta if state is True else self.current_volume - delta
        if volume_to_set > MAX_VOLUME:
            # Set volume to max instead
            logging.error('Change volume: requested volume ({}) over max ({})'.format(volume_to_set, MAX_VOLUME))
            lgtv_call('setVolume {}'.format(volume_to_set), 'Volume set to max volume of {}'.format(MAX_VOLUME))
        else:
            lgtv_call('setVolume {}'.format(volume_to_set), 'Volume changed from {} to {}'.format(self.current_volume, volume_to_set))

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

        # Volume controls
        elif (name == 'volume' and state is True) or (name == 'mute' and state is False):
            if self.muted is True:
                # Volume up is the only I way I know how to unmute
                lgtv_call('volumeUp')
                lgtv_call('volumeDown', 'Turned off mute')  # Volume down to maintain same volume level
            else:
                logging.info('Asked to unmute, but already unmuted')
        elif (name == 'volume' and state is False) or (name == 'mute' and state is True):
            if self.muted is False:
                lgtv_call('mute muted', 'Turned on mute')
            else:
                logging.info('Asked to mute, but already muted')
        elif name in self.set_volume_controls:
            self.set_volume(name)
        elif name in self.change_volume_controls:
            self.change_volume(name, state)

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
    fauxmo.DEBUG = True if LOG_LEVEL == logging.DEBUG else False
    poller = fauxmo.poller()
    listener = fauxmo.upnp_broadcast_responder()
    listener.init_socket()
    poller.add(listener)

    # Register the device callback as a fauxmo handler
    device_handler = device_handler()
    device_handler.init_triggers()
    for trigger, port in device_handler.triggers.items():
        fauxmo.fauxmo(trigger, listener, poller, None, port, device_handler)

    # Loop and poll for incoming Alexa device requests
    logging.debug('Entering fauxmo polling loop')
    while True:
        try:
            device_handler.check_volume_status()
            poller.poll(100)
        except Exception, e:
            logging.critical('Critical exception: {}'.format(e))
            break
