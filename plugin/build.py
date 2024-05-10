from TouchPortalAPI import tppbuild

pluginFileName = "TPLinkTapoPlugin"

PLUGIN_MAIN = pluginFileName + ".py"

PLUGIN_EXE_NAME = pluginFileName

PLUGIN_EXE_ICON = r"icon.ico"

PLUGIN_ENTRY = PLUGIN_MAIN

PLUGIN_ENTRY_INDENT = 2

PLUGIN_ROOT = pluginFileName

PLUGIN_ICON = r"icon-24.png"

OUTPUT_PATH = r"../build"

import TPLinkTapoPlugin
PLUGIN_VERSION = TPLinkTapoPlugin.__version__

ADDITIONAL_FILES = [
    "plugin-conf.txt"
]

ADDITIONAL_PYINSTALLER_ARGS = [
    "--log-level=WARN"
]

if __name__ == "__main__":
    tppbuild.runBuild()