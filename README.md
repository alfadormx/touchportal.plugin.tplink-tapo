# touchportal.plugin.tplink-tapo
Touch Portal plugin to control TPLink Tapo lights


## environment setup instructions
### on windows
1. Install Python 'at least version 3.12'
    ```Shell
    winget install --id=Python.Python.3.12  -e
    ```
2. Execute pip3 on root folder to install dependencies
    ```Shell
    pip3 install -r requirements.txt
    ```
3. Execute this command to package plugin
    ```Shell
    tppbuild plugin/build.py
    ```

### note about plugin-conf.txt
This file only configures the plugin execution, it is used when launching the executable.
```Shell
-d
-l=TPLinkTapoPlugin.log
-s=stdout
```
- -d: will output 'verbose' logs in debug mode
- -l: the name of the .log file (will be stored in %TouchPortalAPPDataFolder%/plugins.TPLinkTapoPlugin/)
- -s: the logStream type, if stderr = sys.stderr, stdout = sys.stdout

In any case you will be able to see logs too on TP's Logs tab.

### lights config file
JSON file with the light's 'pseudo' and IP address:
```json
{
    "Light #1": "127.0.0.1",
    "Light #2": "127.0.0.2"
}
```