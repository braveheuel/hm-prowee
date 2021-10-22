# hm-prowee

Communicate with Homegear server over XML-RPC. This script was designed to be able to set the temperature config of a "HM-CC-RT-DN"-Devide.

## Usage

    usage: hm-prowee.py [-h] [-s SERVER] [-u USER] [-p PORT] [-P PASSWORD] [-c CONFIG]
                        {list,print-config,print-temp,set-temp} ...
    
    Communicate with homegear.
    
    positional arguments:
      {list,print-config,print-temp,set-temp}
        list                Print list of devices
        print-config        Print current config
        print-temp          Print current temperature configuration
        set-temp            Set Device Temperature Configuration
    
    optional arguments:
      -h, --help            show this help message and exit
      -s SERVER, --server SERVER
                            server to use
      -u USER, --user USER  user
      -p PORT, --port PORT  xmlrpc port
      -P PASSWORD, --password PASSWORD
                            password for server/user, if empty or not set in the configuration, ask user
      -c CONFIG, --config CONFIG
                            configuration file instead of default config

* `USER` is the user created in homegear to connect to, follow the [homegear documentation on user management](https://www.homegear.eu/index.php/Create_or_Delete_Users_Using_Homegear%27s_Command_Line_Interface)
* the password for the connection will be prompted after execution of the program, if not set as parameter or inside  the config
* `SERVER` specifies the address of your homegear server as hostname or IP (`homegearpi.local`, `localhost` or `192.168.1.1`), not in URL Syntax (like "http://example.com")
* `PORT` is the RPC server port
* `CONFIG` is the config file to be read. If not set, the default config file is `$HOME/.config/hm-prowee/config`.

The command line parameter take precedence over the values in the config file. For configuration options see section [Configuration File](#configuration-file)

There are two default ports to use with homegear (0.60). Connnections are SSL encrypted on both `2002` and `2003`. **Attention:** Only the later actually verifies the provided username and password. For further details check and edit `/etc/homegear/rpcservers.conf`.

The `list`-command will list all devices with type "0x95", which means the "HM-CC-RT-DN"-Devices.

The `print-config` will print the actual config of the `<id>`.

The `print-temp` command will print the current temperature data of the device with `id` and may act as a starting point to get the current schedule as a temperature file.

The `set-temp` command will then set the device with the `id` the temperature config from the `file`. For the syntax of the file see below.

## Configuration File

The configuration file location is `$HOME/.config/hm-prowee/config`. Example config:

    [main]
    server = 192.168.1.234
    port = 2002
    user = homegearuser
    password = homegear

The section `main` can contain `server`, `port`, `user` and `password`.
Command line arguments take precedence over the config file.
The `password` key can be skipped. If not present or not specified in the command line, the password is asked.

## Syntax of the Temperature file

Example file:

    MONDAY = 17.0 > 15:00; 20.0 > 19:00; 19.0 > 24:00;
    TUESDAY = 17.0 > 15:00; 20.0 > 19:00; 19.0 > 24:00;
    WEDNESDAY = 17.0 > 15:00; 20.0 > 19:00; 19.0 > 24:00;
    THURSDAY = 17.0 > 15:00; 20.0 > 19:00; 19.0 > 24:00;
    FRIDAY = 17.0 > 15:00; 20.0 > 19:00; 19.0 > 24:00;
    SATURDAY = 17.0 > 09:00; 19.5 > 19:00; 19.0 > 24:00;
    SUNDAY = 17.0 > 10:00; 19.5 > 19:00; 19.0 > 24:00;

The lines should start with the day of week. It should be uppercase.

After the equal sign there can be 13 sets temperature intervals. This number is limited by the device itself.

The sets should be read as `<temperature> until <time>`. The first interval starts at 00:00. So the line for "MONDAY" reads as "set 17°C until 15:00, then set it to 20°C until 19:00, then 19°C until 24:00". The last set should always last until 24:00. The intervals should be consecutive.
There no checking included in the script (yet)!
