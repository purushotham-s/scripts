#!/usr/bin/python

from integralstor import networking
import os, socket, sys, subprocess

def get_iface():
    iface = {}
    interfaces, err = networking.get_interfaces()
    if interfaces:
        for name, interface in interfaces.items():
            if name.startswith('lo'):
                continue
            if 'AF_INET' in interface['addresses']:
                iface[name] = interface['addresses']['AF_INET'][0]['addr']
    else:
        print 'Error reading interfaces: %s' % err
    return iface

def add_to_hosts(ip, hostname):
    cmd = 'ping -c 1 %s' % ip
    with open('os.devnull', 'wb') as devnull:
        ping_response = subprocess.call(cmd, shell=True, stdout=devnull, stderr=subprocess.STDOUT)
    if ping_response == 0:
        print 'Host reachable, adding entry in hosts file..'
        hosts_file = open('/etc/hosts', 'a')
        hosts_file.write('%s\t%s\n' % (ip, hostname))
        hosts_file.close()
        return 0
    else:
        print 'Host is unreachable!'
        return 1

if __name__ == '__main__':
    try:
        hostname = sys.argv[1]
    except IndexError:
        hostname = socket.gethostname()
    try:
        ip = sys.argv[2]
    except IndexError:
       ip = None
    if ip:
        add_to_hosts(ip, hostname)
    else:
        ifaces = get_iface()
	print "Interfaces:"
        for iface in ifaces.keys():
            print '%s: %s' % (iface, ifaces[iface])
        choice = raw_input("Enter the interface name to bind its IP address to %s: " % hostname)
        add_to_hosts(ifaces[choice], hostname)

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
