#!/usr/bin/env bash

ARGS=("$@")

# Host home path
HOSTHOME=/home/$USER
if [[ "$OSTYPE" == "darwin"* ]]; then
    # Mac OSX
    HOSTHOME=/Users/$USER
fi

# Make sure processes in the container can connect to the x server
# Necessary so gazebo can create a context for OpenGL rendering (even headless)
XAUTH=/tmp/.docker.xauth
if [ ! -f $XAUTH ]; then
    xauth_list=$(xauth nlist $DISPLAY)
    xauth_list=$(sed -e 's/^..../ffff/' <<<"$xauth_list")
    if [ ! -z "$xauth_list" ]; then
        echo "$xauth_list" | xauth -f $XAUTH nmerge -
    else
        touch $XAUTH
    fi
    chmod a+r $XAUTH
fi

# Prevent executing "docker run" when xauth failed.
if [ ! -f $XAUTH ]; then
    echo "[$XAUTH] was not properly created. Exiting..."
    exit 1
fi

BASH_OPTION=bash

docker run \
    -it \
    --rm \
    -e DISPLAY \
    -e QT_X11_NO_MITSHM=1 \
    -e XAUTHORITY=$XAUTH \
    -v "$XAUTH:$XAUTH" \
    -v "$HOSTHOME/duckietown-shell-commands:/home/arg/.dt-shell/commands-multi/daffy" \
    -v "$HOSTHOME/.ssh:/home/arg/.ssh" \
    -v "/tmp/.X11-unix:/tmp/.X11-unix" \
    -v "/etc/localtime:/etc/localtime:ro" \
    -v "/dev:/dev" \
    -v "/var/run/docker.sock:/var/run/docker.sock" \
    -w "/home/arg/.dt-shell/commands-multi/daffy" \
    --user "arg:arg" \
    --name duckietown-shell-commands \
    --network host \
    --privileged \
    --security-opt seccomp=unconfined \
    argnctu/dts:latest \
    $BASH_OPTION
