#!/bin/sh

IP_HEADER=$(hostname -i | cut -d . -f1-3)
ROUTER=$IP_HEADER".254"

ip route del default
ip route add default via $ROUTER

python manage.py runserver 0.0.0.0:8000 --noreload --nothreading
