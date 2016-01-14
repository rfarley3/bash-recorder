#!/usr/bin/env bash

# edit bash_recorder_service: DAEMON_OPTS="--ssl --cert <cert-file> --log <log-file>"
sudo cp bash_recorder_service.sh /etc/init.d/bashrecorder
sudo update-rc.d bashrecorder defaults
