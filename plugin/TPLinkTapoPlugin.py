import sys
import TouchPortalAPI as TP

from argparse import ArgumentParser

from TouchPortalAPI.logger import Logger

from tapo import ApiClient
from tapo.requests import Color

__version__ = 1.0

PLUGIN_ID = "mx.alfaor.touchportal.TPLinkTapoPlugin"

TP_PLUGIN_INFO = {
    'sdk': 3,
    'version': int(float(__version__) * 100),  # TP only recognizes integer version numbers
    'name': "TPLink Tapo - alFadorMX",
    'id': PLUGIN_ID,
    "plugin_start_cmd": "%TP_PLUGIN_FOLDER%TPLinkTapoPlugin\\TPLinkTapoPlugin.exe @plugin-conf.txt",
    'configuration': {
        'colorDark': "#203060",
        'colorLight': "#4070F0",
        'parentCategory': "homeautomation"
    },
    "doc": {
        "repository": "alfadormx:touchportal.plugin.tplink-tapo"
    }
}

TP_PLUGIN_SETTINGS = {
    'configFile': {
        'name': "Config File Path",
        'type': "text",
        'default': "",
        'readOnly': False,  # this is also the default
        "doc": "File Path to Configuration File",
        'value': None  
    },
    'username': {
        'name': "Topo Username",
        'type': "text",
        'default': "",
        'readOnly': False,  # this is also the default
        "doc": "Username used to connect to TOPO light",
        'value': None  
    },
    'password': {
        'name': "Topo Password",
        'type': "text",
        'default': "",
        'readOnly': False,  # this is also the default
        "doc": "Password used to connect to TOPO light",
        'value': None  
    },
}

TP_PLUGIN_CATEGORIES = {
    "general" : {
        'id': PLUGIN_ID + ".general",
        'name': TP_PLUGIN_INFO['name'],
        'imagepath': "%TP_PLUGIN_FOLDER%TPLinkTapoPlugin/icon-24.png"
    }
}

TP_PLUGIN_ACTIONS = {
    'OnOffTrigger': {
        'category': "general",
        'id': PLUGIN_ID + ".Actions.OnOffTrigger",
        'name': "Turn Device Off and On",
        'prefix': TP_PLUGIN_CATEGORIES['general']['name'],
        'type': "communicate",
        'tryInline': True,
        "doc": "Turn Device Off and On",
        'format': "Turn $[2] $[1]",
        'data': {
            'on&off': {
                'id': PLUGIN_ID + ".Actions.OnOffTrigger.Data.On&Off",
                'type': "choice",
                'label': "choice",
                "valueChoices": [
                    "OFF",
                    "ON"
                ]
            },
            'deviceList': {
                'id': PLUGIN_ID + ".Actions.OnOffTrigger.Data.DeviceList",
                'type': "choice",
                'label': "choice",
                "valueChoices": []
            },
        }
    },
    'Toggle': {
        'category': "general",
        'id': PLUGIN_ID + ".Actions.Toggle",
        'name': "Toggle Device",
        'prefix': TP_PLUGIN_CATEGORIES['general']['name'],
        'type': "communicate",
        'tryInline': True,
        "doc": "Toggle Device",
        'format': "Toggle $[1]",
        'data': {
            'deviceList': {
                'id': PLUGIN_ID + ".Actions.Toggle.Data.DeviceList",
                'type': "choice",
                'label': "choice",
                "valueChoices": []
            },
            'unusedData': {
                'id': PLUGIN_ID + ".Actions.UnusedData",
                'type': "number",
                'label': "UnusedData",
                "default": "50"
            },
        }
    },
    'Bright': {
        'category': "general",
        'id': PLUGIN_ID + ".Actions.Bright",
        'name': "Change Brightness",
        'prefix': TP_PLUGIN_CATEGORIES['general']['name'],
        'type': "communicate",
        'tryInline': True,
        "doc": "Change Brightness",
        'format': "Change $[1] to brightness $[2] %",
        'data': {
            'deviceList': {
                'id': PLUGIN_ID + ".Actions.Bright.Data.DeviceList",
                'type': "choice",
                'label': "choice",
                "valueChoices": []
            },
            'bright': {
                'id': PLUGIN_ID + ".Actions.Bright.Data.Bright",
                'type': "number",
                'minValue': 0,
                'maxValue': 100,
                'allowDecimals': False,
                'label': "Brightness",
                "default": 100
            },
        }
    },
    'RGB': {
        'category': "general",
        'id': PLUGIN_ID + ".Actions.RGB",
        'name': "Change Color",
        'prefix': TP_PLUGIN_CATEGORIES['general']['name'],
        'type': "communicate",
        'tryInline': True,
        "doc": "Change Brightness",
        'format': "Change $[1] to color $[2]",
        'data': {
            'deviceList': {
                'id': PLUGIN_ID + ".Actions.RGB.Data.DeviceList",
                'type': "choice",
                'label': "choice",
                "valueChoices": []
            },
            'rgb': {
                'id': PLUGIN_ID + ".Actions.RGB.Data.RGB",
                'type': "color",
                'label': "color",
                'default': "#000000FF"
            },
        }
    },
}

TP_PLUGIN_STATES = {}

TP_PLUGIN_EVENTS = {}

try:
    TPClient = TP.Client(
        pluginId = PLUGIN_ID,
        sleepPeriod = 0.05,
        autoClose = True,
        checkPluginId = True,
        maxWorkers = 4,
        updateStatesOnBroadcast = False,
    )
except Exception as e:
    sys.exit(f"Could not create TP Client, exiting. Error was:\n{repr(e)}")

g_log = Logger(name = PLUGIN_ID)


def handleSettings(settings, on_connect=False):
    # settings flatteting
    settings = { list(settings[i])[0] : list(settings[i].values())[0] for i in range(len(settings)) }
    if (value := settings.get(TP_PLUGIN_SETTINGS['example']['name'])) is not None:
        TP_PLUGIN_SETTINGS['example']['value'] = value

## TP Client event handler callbacks

# Initial connection handler
@TPClient.on(TP.TYPES.onConnect)
def onConnect(data):
    g_log.info(f"Connected to TP v{data.get('tpVersionString', '?')}, plugin v{data.get('pluginVersion', '?')}.")
    g_log.debug(f"Connection: {data}")
    if settings := data.get('settings'):
        handleSettings(settings, True)

# Settings handler
@TPClient.on(TP.TYPES.onSettingUpdate)
def onSettingUpdate(data):
    g_log.debug(f"Settings: {data}")
    if (settings := data.get('values')):
        handleSettings(settings, False)

# Action handler
@TPClient.on(TP.TYPES.onAction)
def onAction(data):
    g_log.debug(f"Action: {data}")
    if not (action_data := data.get('data')) or not (aid := data.get('actionId')):
        return
    pass

# Shutdown handler
@TPClient.on(TP.TYPES.onShutdown)
def onShutdown(data):
    g_log.info('Received shutdown event from TP Client.')

# Error handler
@TPClient.on(TP.TYPES.onError)
def onError(exc):
    g_log.error(f'Error in TP Client event handler: {repr(exc)}')

## main

def main():
    global TPClient, g_log
    ret = 0  # sys.exit() value
    
    logFile = f"./{PLUGIN_ID}.log"
    logStream = sys.stdout

    parser = ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument("-d", action='store_true', help="Use debug logging.")
    parser.add_argument("-w", action='store_true', help="Only log warnings and errors.")
    parser.add_argument("-q", action='store_true', help="Disable all logging (quiet).")
    parser.add_argument("-l", metavar="<logfile>", help=f"Log file name (default is '{logFile}'). Use 'none' to disable file logging.")
    parser.add_argument("-s", metavar="<stream>", help="Log to output stream: 'stdout' (default), 'stderr', or 'none'.")

    opts = parser.parse_args()
    del parser

    opts.l = opts.l.strip() if opts.l else 'none'
    opts.s = opts.s.strip().lower() if opts.s else 'stdout'
    print(opts)

    logLevel = "INFO"
    if opts.q: logLevel = None
    elif opts.d: logLevel = "DEBUG"
    elif opts.w: logLevel = "WARNING"

    if opts.l:
        logFile = None if opts.l.lower() == "none" else opts.l
    if opts.s:
        if opts.S == "stderr": logStream = sys.stderr
        elif opts.s == "stdout": logStream = sys.stdout
        else: logStream = None

    TPClient.setLogFile(logFile)
    TPClient.setLogStream(logStream)
    TPClient.setLogLevel(logLevel)

    g_log.info(f"Starting {TP_PLUGIN_INFO['name']} v{__version__} on {sys.platform}.")

    # Let's GO !!!!
    try:
        TPClient.connect()
        g_log.info('TP Client closed.')
    except KeyboardInterrupt:
        g_log.warning("Caught keyboard interrupt, exiting.")
    except Exception:
        from traceback import format_exc
        g_log.error(f"Exception in TP Client:\n{format_exc()}")
        ret = -1
    finally:
        TPClient.disconnect()
    
    del TPClient

    g_log.info(f"{TP_PLUGIN_INFO['name']} stopped.")
    return ret


if __name__ == "__main__":
    sys.exit(main())
