FROM alpine:latest
RUN apk add --no-cache iptables
CMD sh -c "echo 1 > /proc/sys/net/ipv4/ip_forward && \
            iptables -A FORWARD -i eth0 -o eth1 -j ACCEPT && \
            iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT && \
            iptables -t nat -A POSTROUTING -o eth1 -j MASQUERADE && \
            tail -f /dev/null"
