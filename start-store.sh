#!/bin/bash

#screen -dmS store ./store_xmpp.py -j user@host -p password

screen -dmS http ./tile_server.py

echo "store agent and tile server started in screen. use 'screen -ls' to view..."
