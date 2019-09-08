#!/bin/bash

get_remote_os() {
	echo -e "\nScan done on `date +%d%m%Y%H%M`:\n" >> scan_out
	HOST_OS=""
	
	for IP in $@;do
		if [[ ! $IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]];then
			echo "$IP is not a valid IPv4 address"
			usage_info
			exit 1
		fi
		echo "Performing nmap scan on $IP"
		OUT=$( nmap -O $IP | grep "OS details" | cut -d ':' -f2 )
		echo "Scan complete - $OUT is running on $IP" 
		echo "$IP --- $OUT" >> scan_out
	done	
}

usage_info() {
	echo "$0 checks and returns the name of the Operating System running on a remote host."
	echo "Useage: sudo $0 <IP_ADDR1> <IP_ADDR2> ... "
	echo "Example: sudo ./get_remote_os 192.168.1.1"
}

check_requirements() {
	if [[ $EUID -ne 0 ]];then
		echo "You have to run this script using sudo or as the root user. See:"
		usage_info
		exit 1
	fi

 	if [[ $# -le 0 ]];then
                usage_info
                exit 1
        fi

	if [[ ! -f `which nmap` ]];then
		echo -e "nmap was not found on this computer. This script requires nmap to function.\n 
		Please install nmap using your distros package manager.\nExample:\n\t$ sudo apt-get 
		install nmap # on ubuntu and debian systems.\n\t$ sudo yum install nmap # on Centos 
		and Redhat systems."
		exit 1
	fi
}

check_requirements $#
get_remote_os $@
