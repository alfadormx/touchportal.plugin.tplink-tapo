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
    "General" : {
        'id': PLUGIN_ID + ".general",
        'name': TP_PLUGIN_INFO['name'],
        'imagepath': "%TP_PLUGIN_FOLDER%TPLinkTapoPlugin/icon-24.png"
    }
}

TP_PLUGIN_ACTIONS = {
    'example': {
        # 'category' is optional, if omitted then this action will be added to all, or the only, category(ies)
        'category': "General",
        'id': PLUGIN_ID + ".act.example",
        'name': "Set Example Action",
        'prefix': TP_PLUGIN_CATEGORIES['General']['name'],
        'type': "communicate",
        'tryInline': True,
        "doc": "Example doc string",
        # 'format' tokens like $[1] will be replaced in the generated JSON with the corresponding data id wrapped with "{$...$}".
        # Numeric token values correspond to the order in which the data items are listed here, while text tokens correspond
        # to the last part of a dotted data ID (the part after the last period; letters, numbers, and underscore allowed).
        'format': "Set Example State Text to $[text] and Color to $[2]",
        'data': {
            'text': {
                'id': PLUGIN_ID + ".act.example.data.text",
                # "text" is the default type and could be omitted here
                'type': "text",
                'label': "Text",
                'default': "Hello World!"
            },
            'color': {
                'id': PLUGIN_ID + ".act.example.data.color",
                'type': "color",
                'label': "Color",
                'default': "#818181FF"
            },
        }
    },
}

TP_PLUGIN_STATES = {

}

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
