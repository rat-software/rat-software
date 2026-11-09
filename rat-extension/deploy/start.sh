#!/bin/sh
set -e
: "${DISPLAY:=:99}"; : "${SCREEN:=1366x850x24}"
EXT=/opt/rat-extension
PROFILE=/data/profile

# Chrome derives the id of an unpacked extension from its absolute path.
EXT_ID=$(printf '%s' "$EXT" | openssl dgst -sha256 -binary | od -An -tx1 -v | tr -d ' \n' | cut -c1-32 | tr '0-9a-f' 'a-p')
echo "Extension id: $EXT_ID"

rm -f /tmp/.X99-lock
Xvfb "$DISPLAY" -screen 0 "$SCREEN" -nolisten tcp &
sleep 1
fluxbox >/dev/null 2>&1 &

if [ -n "$VNC_PASSWORD" ]; then
  x11vnc -storepasswd "$VNC_PASSWORD" /tmp/vncpass >/dev/null
  x11vnc -display "$DISPLAY" -rfbauth /tmp/vncpass -forever -shared -quiet -localhost &
else
  echo "WARNING: VNC_PASSWORD is empty. Only expose port 6080 on localhost / through an SSH tunnel."
  x11vnc -display "$DISPLAY" -nopw -forever -shared -quiet -localhost &
fi
websockify --web=/usr/share/novnc 6080 localhost:5900 &

# Remove stale profile locks after a crash/unclean stop
rm -f "$PROFILE"/Singleton* 2>/dev/null || true

while true; do
  chromium \
    --user-data-dir="$PROFILE" \
    --no-sandbox --disable-dev-shm-usage --no-first-run --no-default-browser-check \
    --disable-extensions-except="$EXT" --load-extension="$EXT" \
    --window-size=1366,850 --window-position=0,0 \
    --disable-background-timer-throttling --disable-renderer-backgrounding --disable-backgrounding-occluded-windows \
    "chrome-extension://$EXT_ID/sidepanel.html" || true
  echo "Chromium exited, restarting in 5 s"
  sleep 5
done
