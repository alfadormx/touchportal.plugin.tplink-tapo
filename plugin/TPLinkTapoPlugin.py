import colorsys
from functools import wraps
import sys
import TouchPortalAPI as TP
import json
import asyncio
from typing import Any, Awaitable, Dict, Optional, TypeVar
from argparse import ArgumentParser
from TouchPortalAPI.logger import Logger
from tapo import ApiClient

__version__ = 1.0

PLUGIN_ID = "mx.alfador.touchportal.TPLinkTapoPlugin"

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
        'name': "Username",
        'type': "text",
        'default': "",
        'readOnly': False,  # this is also the default
        "doc": "Username used to connect to TOPO light",
        'value': None  
    },
    'password': {
        'name': "Password",
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
    'RGB-Bright': {
        'category': "general",
        'id': PLUGIN_ID + ".Actions.RGB-Bright",
        'name': "Change Color and Brightness",
        'prefix': TP_PLUGIN_CATEGORIES['general']['name'],
        'type': "communicate",
        'tryInline': True,
        "doc": "Change Brightness",
        'format': "Change $[1] to color $[2] and brightness $[3]",
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
g_device_list = {}
g_tapo_client = None

R = TypeVar("R")

def async_to_sync(func: Awaitable[R]) -> R:
    '''Wraps `asyncio.run` on an async function making it sync callable.'''
    if not asyncio.iscoroutinefunction(func):
        raise TypeError(f"{func} is not a coroutine function")
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return asyncio.get_event_loop().run_until_complete(func(*args, **kwargs))
        except RuntimeError:
            return asyncio.new_event_loop().run_until_complete(func(*args, **kwargs))
    return wrapper

@async_to_sync
async def handle_settings(settings, on_connect=False):
    settings = { list(settings[i])[0] : list(settings[i].values())[0] for i in range(len(settings)) }
    config_value = settings.get(TP_PLUGIN_SETTINGS['configFile']['name'])
    username_value = settings.get(TP_PLUGIN_SETTINGS['username']['name'])
    password_value = settings.get(TP_PLUGIN_SETTINGS['password']['name'])

    if config_value and config_value.strip():
        TP_PLUGIN_SETTINGS['configFile']['value'] = config_value.strip()
        try:
            read_config_file(config_value.strip())
            update_choices()
        except Exception as e:
            g_log.warning(f"Failed to process config file: {e}")
    if username_value:
        TP_PLUGIN_SETTINGS['username']['value'] = username_value
    if password_value:
        TP_PLUGIN_SETTINGS['password']['value'] = password_value

    if username_value and password_value:
        await initialize_tapo(username_value, password_value)

async def initialize_tapo(username, password) -> None:
    global g_tapo_client

    g_tapo_client = ApiClient(username, password)
    g_log.debug(f"initializeTapo: tapoClient is set with u> {username} & p> {password}")

    tasks = [fetch_device(g_tapo_client, device) for device in g_device_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for device, result in zip(g_device_list, results):
        if isinstance(result, Exception):
            device["device"] = None
        else:
            device["device"] = result

async def fetch_device(client: ApiClient, device_info: Dict[str, Any]) -> Optional[Any]:
    try:
        g_log.debug(f"trying fetch_device: d> {device_info['name']} & ip> {device_info['ipaddress']}")
        device = await client.l630(device_info["ipaddress"])
        g_log.debug(f"fetch_device: d> {device_info['name']} & ip> {device_info['ipaddress']} OK!")
        return device
    except Exception as e:
        g_log.warning(f"Error fetching data for {device_info['name']}: {e}")
        return None

def read_config_file(file_path) -> None:
    global g_device_list

    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            g_device_list = [{'name': name, 'ipaddress': ip} for name, ip in data.items()]
            g_log.debug(f"Config file: {file_path} read with info {data}")
    except Exception as e:
        g_log.warning(f"Error reading file {file_path}: {repr(e)}")
        return []

def update_choices() -> None:
    global g_device_list
    choices = [device['name'] for device in g_device_list]

    TPClient.choiceUpdate(TP_PLUGIN_ACTIONS['OnOffTrigger']['data']['deviceList']['id'], choices)
    TPClient.choiceUpdate(TP_PLUGIN_ACTIONS['Toggle']['data']['deviceList']['id'], choices)
    TPClient.choiceUpdate(TP_PLUGIN_ACTIONS['Bright']['data']['deviceList']['id'], choices)
    TPClient.choiceUpdate(TP_PLUGIN_ACTIONS['RGB']['data']['deviceList']['id'], choices)

@async_to_sync
async def on_off_trigger_action(action_data:list) -> None:
    onOff = TPClient.getActionDataValue(action_data, TP_PLUGIN_ACTIONS['OnOffTrigger']['data']['on&off']['id'])
    device_name = TPClient.getActionDataValue(action_data, TP_PLUGIN_ACTIONS['OnOffTrigger']['data']['deviceList']['id'])
    light = get_device_by_name(device_name)
    g_log.debug(f"on_off_trigger: a> {onOff} d> {device_name} l> {repr(light)}")

    if (onOff == "ON" and light):
        await light.on()
    else:
        await light.off()

@async_to_sync
async def toggle_action(action_data:list) -> None:
    device_name = TPClient.getActionDataValue(action_data, TP_PLUGIN_ACTIONS['Toggle']['data']['deviceList']['id'])
    light = get_device_by_name(device_name)
    g_log.debug(f"toggle: d> {device_name} l> {repr(light)}")

    if (light):
        device_info = await light.get_device_info()
        g_log.debug(f"device_info: {repr(device_info)}")
        if (device_info.device_on):
            await light.off()
        else:
            await light.on()

@async_to_sync
async def brightness_action(action_data:list) -> None:
    device_name = TPClient.getActionDataValue(action_data, TP_PLUGIN_ACTIONS['Bright']['data']['deviceList']['id'])
    brightness = TPClient.getActionDataValue(action_data, TP_PLUGIN_ACTIONS['Bright']['data']['bright']['id'])
    light = get_device_by_name(device_name)
    g_log.debug(f"brightness: d> {device_name} b> {brightness}% l> {repr(light)}")
    
    if (light):
        await light.set_brightness(brightness)

@async_to_sync
async def rgb_action(action_data:list) -> None:
    device_name = TPClient.getActionDataValue(action_data, TP_PLUGIN_ACTIONS['RGB']['data']['deviceList']['id'])
    rgb = TPClient.getActionDataValue(action_data, TP_PLUGIN_ACTIONS['RGB']['data']['rgb']['id'])
    light = get_device_by_name(device_name)

    g_log.debug(f"rgb: d> {device_name} r> {rgb} l> {repr(light)}")

    if (light):
        hue, saturation = hex_to_hue_saturation(rgb)
        await light.set_hue_saturation(hue, saturation)

@async_to_sync
async def rgb_bright_action(action_data:list) -> None:
    device_name = TPClient.getActionDataValue(action_data, TP_PLUGIN_ACTIONS['RGB-Bright']['data']['deviceList']['id'])
    rgb = TPClient.getActionDataValue(action_data, TP_PLUGIN_ACTIONS['RGB-Bright']['data']['rgb']['id'])
    brightness = TPClient.getActionDataValue(action_data, TP_PLUGIN_ACTIONS['RGB-Bright']['data']['bright']['id'])
    light = get_device_by_name(device_name)

    g_log.debug(f"rgb - bright: d> {device_name} r> {rgb} b> {brightness} l> {repr(light)}")    

    if (light):
        hue, saturation = hex_to_hue_saturation(rgb)
        await light.set().brightness(brightness).hue_saturation(hue, saturation).send(light)

def hex_to_hue_saturation(hex_color):
    hex_color = hex_color.lstrip("#")
    r, g, b, a = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16), int(hex_color[6:8], 16)
    r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
    h, s, _ = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
    hue = max(5, min(255, int(h * 360)))
    saturation = int(s * 100)

    return hue, saturation    

def get_device_by_name(device_name):
    for device in g_device_list:
        if device['name'] == device_name:
            return device['device']  # Returns the ColorLightHandler object
    return None  # Return None if not found

## TP Client event handler callbacks

# Initial connection handler
@TPClient.on(TP.TYPES.onConnect)
def on_connect(data):
    g_log.info(f"Connected to TP v{data.get('tpVersionString', '?')}, plugin v{data.get('pluginVersion', '?')}.")
    g_log.debug(f"Connection: {data}")
    if settings := data.get('settings'):
        handle_settings(settings, True)

# Settings handler
@TPClient.on(TP.TYPES.onSettingUpdate)
def on_setting_update(data):
    g_log.debug(f"Settings: {data}")
    if (settings := data.get('values')):
        handle_settings(settings, False)

# Action handler
@TPClient.on(TP.TYPES.onAction)
def on_action(data):
    g_log.debug(f"Action: {data}")
    if not (action_data := data.get('data')) or not (aid := data.get('actionId')):
        return
    if aid == TP_PLUGIN_ACTIONS['OnOffTrigger']['id']:
        on_off_trigger_action(action_data)
    elif aid == TP_PLUGIN_ACTIONS['Toggle']['id']:
        toggle_action(action_data)
    elif aid == TP_PLUGIN_ACTIONS['Bright']['id']:
        brightness_action(action_data)
    elif aid == TP_PLUGIN_ACTIONS['RGB']['id']:
        rgb_action(action_data)
    elif aid == TP_PLUGIN_ACTIONS['RGB-Bright']['id']:
        rgb_bright_action(action_data)
    else:
        g_log.warning("Got unknown action ID: " + aid)

# Shutdown handler
@TPClient.on(TP.TYPES.onShutdown)
def onShutdown(data):
    g_log.info('Received shutdown event from TP Client.')

# Error handler
@TPClient.on(TP.TYPES.onError)
def onError(exc):
    g_log.warning(f'Error in TP Client event handler: {repr(exc)}')

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
        if opts.s == "stderr": logStream = sys.stderr
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
        g_log.warning(f"Exception in TP Client:\n{format_exc()}")
        ret = -1
    finally:
        TPClient.disconnect()
    
    del TPClient

    g_log.info(f"{TP_PLUGIN_INFO['name']} stopped.")
    return ret

if __name__ == "__main__":
    sys.exit(main())
