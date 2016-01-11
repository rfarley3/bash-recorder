SESSID=$(cat /dev/urandom | env LC_CTYPE=C tr -dc 'a-zA-Z0-9' | fold -w 10 | head -n 1)
export SESSID
SESSIP=$(ifconfig en0 2>&1 | grep inet[^6] | awk '{print $2}')
export SESSIP
function log2ctfref
{
    [ -n "$COMP_LINE" ] && return  # do nothing if completing
    [ "$BASH_COMMAND" = "$PROMPT_COMMAND" ] && return # don't cause a preexec for $PROMPT_COMMAND
    declare cmd
    # cmd=$(printf %q "$BASH_COMMAND" | base64)
    cmd=$(echo -n $BASH_COMMAND | base64)
    sess=$$.$PPID.$SESSID
    ts=$(date +%s)
    # echo "cmd: $cmd u: $USER sess: $sess ip: $SESSIP"
    # echo post_data: $post_data
    curl -s \
        --connect-timeout 5 \
        -H "Accept: application/json" \
        -H "Content-Type:application/json" \
        -X POST http://127.0.0.1:9999/cmd \
        -d '{"cmd":"'"$cmd"'","ts":"'"$ts"'","src":{"user":"'"$USER"'","session":"'"$sess"'","ip":"'"$SESSIP"'"}}' \
        2>&1 > /dev/null
}
trap log2ctfref DEBUG
