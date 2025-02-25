#!/bin/sh

IP_HEADER=$(hostname -i | cut -d . -f1-3)
ROUTER=$IP_HEADER".254"

ip route del default
ip route add default via $ROUTER

ts-node proxy/proxy.ts &

npm run dev

