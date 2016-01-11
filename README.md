```
 ____                      ____                        __
|  _ \                    |  _ \                      / _)
| |_) ) __  ______ _ __   | |_) )____   _____   ___   \ \  ___  ___
|  _ ( /  \/ /  ._) '_ \  |  __/ __) \ / / _ \ / _ \ / _ \/ __)/ _ \
| |_) | ()  < () )| | | | | |  > _) \ v ( (_) ) |_) | (_) > _)| |_) )
|____/ \__/\_\__/ |_| | | |_|  \___) > < \___/|  __/ \___/\___)  __/
                      | |           / ^ \     | |             | |
                      |_|          /_/ \_\    |_|             |_|
```
### bash-recorder

## Install Client
* Paste contents of profile-log2ctfref.sh into /etc/profile
    * Change en0 to your primary ifconfig interface name
    * Change 127.0.0.1 to the IP of your server
* All future bash sessions will be recorded

## Run Server
* `./bash_recorder.py`
	* default log file is bashrec.log
