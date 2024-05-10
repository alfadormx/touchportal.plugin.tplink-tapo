from TouchPortalAPI import tppbuild

pluginFileName = "plugin"

PLUGIN_MAIN = pluginFileName + ".py"

PLUGIN_EXE_NAME = pluginFileName

PLUGIN_EXE_ICON = r"icon.ico"

PLUGIN_ENTRY = PLUGIN_MAIN

PLUGIN_ENTRY_INDENT = 2

PLUGIN_ROOT = pluginFileName

PLUGIN_ICON = r"icon.png"

OUTPUT_PATH = r"../build"

import plugin
PLUGIN_VERSION = plugin.__version__

ADDITIONAL_FILES = []

ADDITIONAL_PYINSTALLER_ARGS = [
    "--log-level=WARN"
]

if __name__ == "__main__":
    tppbuild.runBuild()