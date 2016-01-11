#!/usr/bin/env bash
SESSID=$(cat /dev/urandom | env LC_CTYPE=C tr -dc 'a-zA-Z0-9' | fold -w 10 | head -n 1)
export SESSID
SESSIP=$(ifconfig en0 2>&1 | grep inet[^6] | awk '{print $2}')
export SESSIP
function log2ctfref
{
    [ -n "$COMP_LINE" ] && return
    [ "$BASH_COMMAND" = "$PROMPT_COMMAND" ] && return
    declare cmd
    cmd=$(echo -n $BASH_COMMAND | base64)
    ts=$(date +%s)
    sess=$$.$PPID.$SESSID
    curl -s \
        --connect-timeout 5 \
        -H "Accept: application/json" \
        -H "Content-Type:application/json" \
        -X POST http://127.0.0.1:9999/cmd \
        -d '{"cmd":"'"$cmd"'","ts":"'"$ts"'","src":{"user":"'"$USER"'","session":"'"$sess"'","ip":"'"$SESSIP"'"}}' \
        2>&1 > /dev/null
}
trap log2ctfref DEBUG
