#!/bin/bash -ex

eval "$(dbus-launch --sh-syntax)"
ps -ef | grep dbus | grep -v grep
eval "$(echo | gnome-keyring-daemon --unlock)"
export DBUS_SESSION_BUS_ADDRESS
export GNOME_KEYRING_CONTROL
export SSH_AUTH_SOCK

bash -c "nose2 -v -X --config ./tests/integration_test.cfg  -A 'integration'"
