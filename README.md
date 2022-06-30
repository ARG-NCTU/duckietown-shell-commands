# dts duckiepond

We could setup a few dts commands to setup a device in Duckiepond. This is supposed to run on the laptop on the base station.

## Change to our forked repo

```
$ pip3 install duckietown-shell
$ dts
$ cd ~/.dt-shell/commands-multi/daffy/
$ git remote -v
$ git remote set-url origin git@github.com:ARG-NCTU/duckietown-shell-commands.git
$ git pull
$ pip3 install arg-robotics-tools -U
$ dts duckiepond hello
```

## clone duckie devices yaml

```
$ cd ~/.dt-shell/commands-multi/daffy/
$ git submodule init
$ git submodule update
```

## when you need to update

```
$ cd ~/.dt-shell/commands-multi/daffy
$ git pull
$ cd duckiepond-devices
$ git submodule init
$ git submodule update
```

## dependency

TODO: xbee, ros, etc dependencies

TODO: Or it's even better to add Docker for this. 

TODO: We could also test our nbdev lib here.


## Checking System

TODO: submodule the repo with device.yaml

### Hostname, username, ssh key, 

### Setup network properly (IP, virtual IP, etc)

### Make a Duckietown Device


## Developments and Deployments

### Clone repo and build 

### Environment variables for who I am

### Any robot-specific topic name 

### Docker autorun (Turnkey)

## Tests (arg-veh-machine-test repo)

### dts fleet discover

### Test XBee comm (TODO modify repo)

### Test starting up sensors (procman)



-----------------------


[![CircleCI](https://circleci.com/gh/duckietown/duckietown-shell-commands.svg?style=shield)](https://circleci.com/gh/duckietown/duckietown-shell-commands)



TODO: this should get polished and updated. 

**You need to have successfully installed the Duckietown Shell. If you know what you want to do with it go ahead. Below are some examples of things you can do with the Duckietown Shell** 

## Compile one of the "Duckumentation"

To compile one of the books (e.g. docs-duckumentation but there are many others):

    $ git clone https://github.com/duckietown/docs-duckumentation.git
    $ cd docs-duckumentation
    $ git submodule init
    $ git submodule update
    $ dts docs build

There is an incremental build system. To clean and run from scratch:

    $ dts docs clean
    $ dts docs build
  

## Authenticate a Duckietown Token

Run the command `dts tok set` to set the Duckietown authentication token:

    $ dts tok set  

Instructions will guide you and you will be prompted for the token.

If you already know the token, then you can use:

    $ dts tok set dt1-YOUR-TOKEN
    
### Verifying that a token is valid

To verify that a token is valid, you can use:

    $ dts tok verify dt1-TOKEN-TO-VERIFY
    
This exits with 0 if the token is valid, and writes on standard output the following json:

    {"uid": 3, "expiration": "2018-09-23"}
    
which means that the user is identified as uid 3 until the given expiration date.
 

-----------------------

## Duckiebot setup

### Command for flashing SD card

This command will install DuckieOS on the SD-card:

    $ dts init_sd_card

-----------------------

### Command for starting ROS GUIs

This command will start the ROS GUI container:

    $ dts start_gui_tools <DUCKIEBOT_NAME_GOES_HERE>

-----------------------

### Command for calibrating the Duckiebot

This command will run the Duckiebot calibration procedure:

    $ dts calibrate_duckiebot <DUCKIEBOT_NAME_GOES_HERE>

