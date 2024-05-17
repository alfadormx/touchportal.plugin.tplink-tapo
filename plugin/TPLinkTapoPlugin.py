import colorsys
from functools import wraps
import sys
import TouchPortalAPI as TP
import yaml
import asyncio
from typing import Any, Awaitable, Dict, Optional, TypeVar
from argparse import ArgumentParser
from TouchPortalAPI.logger import Logger
from tapo import ApiClient

# Supported device types
SUPPORTED_DEVICE_TYPES = {
    "L510": ["On_Off", "Toggle", "Bright"],
    "L520": ["On_Off", "Toggle", "Bright"],
    "L610": ["On_Off", "Toggle", "Bright"],
    "L530": ["On_Off", "Toggle", "Bright", "RGB", "ColorTemperature", "RGB_Bright"],
    "L630": ["On_Off", "Toggle", "Bright", "RGB", "ColorTemperature", "RGB_Bright"]
}

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
    'On_Off': {
        'category': "general",
        'id': PLUGIN_ID + ".Actions.On_Off",
        'name': "On / Off",
        'prefix': TP_PLUGIN_CATEGORIES['general']['name'],
        'type': "communicate",
        'tryInline': True,
        "doc": "Turn Device **on** or **off**",
        'format': "Turn $[2] $[1]",
        'data': {
            'on_off': {
                'id': PLUGIN_ID + ".Actions.On_Off.Data.OnOff",
                'type': "choice",
                'label': "choice",
                "valueChoices": [
                    "OFF",
                    "ON"
                ]
            },
            'device_list': {
                'id': PLUGIN_ID + ".Actions.On_Off.Data.DeviceList",
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
        "doc": "Turns **on** or **off** a device accordingly",
        'format': "Toggle $[1]",
        'data': {
            'device_list': {
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
        'name': "Set Brightness",
        'prefix': TP_PLUGIN_CATEGORIES['general']['name'],
        'type': "communicate",
        'tryInline': True,
        "doc": "Set **Brightness** and turns **on** the device",
        'format': "Change $[1] to brightness $[2] %",
        'data': {
            'device_list': {
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
        'name': "Set Color",
        'prefix': TP_PLUGIN_CATEGORIES['general']['name'],
        'type': "communicate",
        'tryInline': True,
        "doc": "Sets the **Color** and turns **on** the device",
        'format': "Set $[1] to color $[2]",
        'data': {
            'device_list': {
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
    'ColorTemperature': {
        'category': "general",
        'id': PLUGIN_ID + ".Actions.ColorTemperature",
        'name': "Set Color Temperature",
        'prefix': TP_PLUGIN_CATEGORIES['general']['name'],
        'type': "communicate",
        'tryInline': True,
        "doc": "Sets the **Color Temperature** and turns **on** the device",
        'format': "Set $[1] color temperature to $[2]",
        'data': {
            'device_list': {
                'id': PLUGIN_ID + ".Actions.ColorTemperature.Data.DeviceList",
                'type': "choice",
                'label': "choice",
                "valueChoices": []
            },
            'temperature': {
                'id': PLUGIN_ID + ".Actions.ColorTemperature.Data.Temperature",
                'type': "number",
                'minValue': 2500,
                'maxValue': 6500,
                'allowDecimals': False,
                'label': "Brightness",
                "default": 2700
            },
        }
    },
    'RGB_Bright': {
        'category': "general",
        'id': PLUGIN_ID + ".Actions.RGB_Bright",
        'name': "Set Color and Brightness",
        'prefix': TP_PLUGIN_CATEGORIES['general']['name'],
        'type': "communicate",
        'tryInline': True,
        "doc": "Sets the **Color** and **Brightness** and turns **on** the device",
        'format': "Set $[1] to color $[2] and brightness $[3]",
        'data': {
            'device_list': {
                'id': PLUGIN_ID + ".Actions.RGB_Bright.Data.DeviceList",
                'type': "choice",
                'label': "choice",
                "valueChoices": []
            },
            'rgb': {
                'id': PLUGIN_ID + ".Actions.RGB_Bright.Data.RGB",
                'type': "color",
                'label': "color",
                'default': "#000000FF"
            },
            'bright': {
                'id': PLUGIN_ID + ".Actions.RGB_Bright.Data.Bright",
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

@async_to_sync
async def handle_settings(settings, on_connect=False):
    settings = { list(settings[i])[0] : list(settings[i].values())[0] for i in range(len(settings)) }
    config_value = settings.get(TP_PLUGIN_SETTINGS['configFile']['name'])
    username_value = settings.get(TP_PLUGIN_SETTINGS['username']['name'])
    password_value = settings.get(TP_PLUGIN_SETTINGS['password']['name'])

    if config_value and config_value.strip():
        TP_PLUGIN_SETTINGS['configFile']['value'] = config_value.strip()
        try:
            device_list = read_config_file(config_value.strip())
            validate_devices(device_list);
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

    tasks = [fetch_device(g_tapo_client, device) for device in g_device_list.values()]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for device, result in zip(g_device_list.values(), results):
        if isinstance(result, Exception):
            device["device"] = None
        else:
            device["device"] = result

async def fetch_device(client: ApiClient, device_info: Dict[str, Any]) -> Optional[Any]:
    try:
        g_log.debug(f"trying fetch_device: d> {device_info['name']} & ip> {device_info['ipaddress']}")
        
        # Select API method based on device type
        if device_info['type'] == 'L510':
            device = await client.l510(device_info["ipaddress"])
        elif device_info['type'] == 'L520':
            device = await client.l520(device_info["ipaddress"])
        elif device_info['type'] == 'L610':
            device = await client.l610(device_info["ipaddress"])
        elif device_info['type'] == 'L530':
            device = await client.l530(device_info["ipaddress"])
        elif device_info['type'] == 'L630':
            device = await client.l630(device_info["ipaddress"])
        else:
            g_log.warning(f"Unsupported device type: {device_info['type']} for device {device_info['ipaddress']}")
            return None

        g_log.debug(f"fetch_device: d> {device_info['name']} & ip> {device_info['ipaddress']} OK!")
        return device
    except Exception as e:
        g_log.warning(f"Error fetching data for {device_info['name']}: {e}")
        return None

def read_config_file(file_path) -> Any:
    device_list = {}

    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
            for device_type, devices in data.items():
                if devices:
                    for device in devices:
                        if 'name' in device and 'ip' in device:
                            device_list[device['name']] = {
                                'name': device['name'],
                                'ipaddress': device['ip'],
                                'type': device_type,
                                'device': None, # it will contain reference to tapo light
                            }
                        else:
                            g_log.warning(f"Device is missing 'name' or 'ip': t> {device_type} d> {device}")
            g_log.debug(f"Config file: {file_path} read: dl> {device_list}")
    except Exception as e:
        g_log.warning(f"Error reading file {file_path}: {repr(e)}")
        return []
    
    return device_list

def validate_devices(device_list) -> None:
    global g_device_list

    for name, device in device_list.items():
        if device['type'] not in SUPPORTED_DEVICE_TYPES:
            g_log.warning(f"Unsupported device type: t> {device['type']} d> {name}")
        else:
            g_device_list[name] = device
    
    g_log.debug(f"Device list validated: gdl> {g_device_list}")

def update_choices() -> None:
    global g_device_list

    all_actions = {action for actions in SUPPORTED_DEVICE_TYPES.values() for action in actions}
    filtered_choices = {action: [] for action in all_actions}

    # Populate the filtered choices based on device capabilities
    for name, device in g_device_list.items():
        for action in SUPPORTED_DEVICE_TYPES[device['type']]:
            filtered_choices[action].append(name)

    TPClient.choiceUpdate(TP_PLUGIN_ACTIONS['On_Off']['data']['device_list']['id'], filtered_choices["On_Off"])
    TPClient.choiceUpdate(TP_PLUGIN_ACTIONS['Toggle']['data']['device_list']['id'], filtered_choices["Toggle"])
    TPClient.choiceUpdate(TP_PLUGIN_ACTIONS['Bright']['data']['device_list']['id'], filtered_choices["Bright"])

    if any(filtered_choices["RGB"]):
        TPClient.choiceUpdate(TP_PLUGIN_ACTIONS['RGB']['data']['device_list']['id'], filtered_choices["RGB"])

    if any(filtered_choices["RGB_Bright"]):
        TPClient.choiceUpdate(TP_PLUGIN_ACTIONS['RGB_Bright']['data']['device_list']['id'], filtered_choices["RGB_Bright"])

    if any(filtered_choices["ColorTemperature"]):
        TPClient.choiceUpdate(TP_PLUGIN_ACTIONS['ColorTemperature']['data']['device_list']['id'], filtered_choices["ColorTemperature"])

## Actions

# Action definitions

async def on_off_action(device_name, light, action_data:list) -> None:
    on_off = TPClient.getActionDataValue(action_data, TP_PLUGIN_ACTIONS['On_Off']['data']['on_off']['id'])

    g_log.debug(f"Action: on_off | a> {on_off} d> {device_name} l> {repr(light)}")

    if (on_off == "ON"):
        await light.on()
    else:
        await light.off()

async def toggle_action(device_name, light) -> None:
    g_log.debug(f"Action: toggle | d> {device_name} l> {repr(light)}")
    
    device_info = await light.get_device_info()
    g_log.debug(f"Action: toggle | device_info: {repr(device_info)}")

    if (device_info.device_on):
        await light.off()
    else:
        await light.on()

async def bright_action(device_name, light, action_data:list) -> None:
    brightness = TPClient.getActionDataValue(action_data, TP_PLUGIN_ACTIONS['Bright']['data']['bright']['id'])
    
    g_log.debug(f"Action brightness | d> {device_name} b> {brightness}% l> {repr(light)}")

    await light.set_brightness(int(brightness))

async def rgb_action(device_name, light, action_data:list) -> None:
    rgb = TPClient.getActionDataValue(action_data, TP_PLUGIN_ACTIONS['RGB']['data']['rgb']['id'])

    hue, saturation = hex_to_hue_saturation(rgb)
    g_log.debug(f"Action rgb | d> {device_name} r> {rgb} h> {hue} s> {saturation} l> {repr(light)}")

    await light.set_hue_saturation(hue, saturation)

async def color_temperature_action(device_name, light, action_data) -> None:
    temperature = TPClient.getActionDataValue(action_data, TP_PLUGIN_ACTIONS['ColorTemperature']['data']['temperature']['id'])

    g_log.debug(f"Action color_temperature | d> {device_name} t> {temperature} l> {repr(light)}")

    await light.set_color_temperature(temperature)

async def rgb_bright_action(device_name, light, action_data:list) -> None:
    rgb = TPClient.getActionDataValue(action_data, TP_PLUGIN_ACTIONS['RGB_Bright']['data']['rgb']['id'])
    brightness = TPClient.getActionDataValue(action_data, TP_PLUGIN_ACTIONS['RGB_Bright']['data']['bright']['id'])

    hue, saturation = hex_to_hue_saturation(rgb)
    g_log.debug(f"Action rgb_bright | d> {device_name} r> {rgb} b> {brightness} h> {hue} s> {saturation} l> {repr(light)}")

    await light.set().brightness(int(brightness)).hue_saturation(hue, saturation).send(light)

# Action map

TP_PLUGIN_ACTION_MAP = {
    TP_PLUGIN_ACTIONS['On_Off']['id']: on_off_action,
    TP_PLUGIN_ACTIONS['Toggle']['id']: toggle_action,
    TP_PLUGIN_ACTIONS['Bright']['id']: bright_action,
    TP_PLUGIN_ACTIONS['RGB']['id']: rgb_action,
    TP_PLUGIN_ACTIONS['ColorTemperature']['id']: color_temperature_action,
    TP_PLUGIN_ACTIONS['RGB_Bright']['id']: rgb_bright_action
}

# Helpers

def hex_to_hue_saturation(hex_color):
    hex_color = hex_color.lstrip("#")
    r, g, b, a = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16), int(hex_color[6:8], 16)
    r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
    h, s, _ = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
    hue = max(1, min(360, int(h * 360)))
    saturation = max(1, min(100, int(s * 100)))

    return hue, saturation

# Perform action

@async_to_sync
async def perform_action(aid:str, action_data:list) -> None:
    device_name = TPClient.getActionDataValue(action_data, TP_PLUGIN_ACTIONS['On_Off']['data']['device_list']['id'])
    light = g_device_list.get(device_name)["device"]

    if not light:
        g_log.debug(f"Action: {aid} | l> Light not found!")
        return
    
    action_func = TP_PLUGIN_ACTION_MAP.get(aid)
    if (action_func):
        await action_func(device_name, light, action_data)
    else:
        g_log.warning(f"Got unknown action ID: {aid}")

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
    g_log.debug(f"Action {data}")
    
    action_data = data.get('data')
    aid = data.get('actionId')

    if not action_data or not aid:
        return
    
    if aid in TP_PLUGIN_ACTION_MAP:
        perform_action(aid, action_data)
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
