#!/bin/bash

configure_nodes(){
	node1_hostname=`hostname`
	if [[ -z $node1_hostname ]] 
	then
	  echo "Hostname not set, please set a hostname for this machine before configuring HA."
	  read -p "Would you like to set hostname now?(y/n)" input
	  case $input in
	    (Y|y) set_hostname;;
	    (N|n) echo "Exiting..";exit;;
	  esac
	else
	  echo "Hostname of this machine is: $node1_hostname"
	  read -p "Would you like to continue with this hostname?(y/n)" input2
	  case $input2 in
	    (Y|y) python configure_hosts.py $node1_hostname;echo 'Done';;
            (N|n) set_hostname;;
          esac
        fi

	while true
	do
	  read -p "Please enter the hostname of 2nd node: " node2_hostname
	  if [[ $node2_hostname == *['!'@#\$%^\&*()_+]* ]]
          then
            echo "$node2_hostname is not a valid hostname, please try again."
            continue
	  else
	    break
	  fi
	done

	while true
	  do
	  read -p "Please enter the IP address of 2nd node: " node2_ip
	  if [[ $node2_ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]
	  then
	    break
	  else
            echo "$node2_ip is not a valid IP address."
            continue
	  fi
	done
	  
	echo "Adding $node2_hostname to hosts file.."
	python configure_hosts.py $node2_hostname $node2_ip
	echo "Authenticating cluster nodes.."
	pcs cluster auth $node1_hostname $node2_hostname -u hacluster -p hacluster
	echo "Setting up cluster.."
	echo "Please enter a name for this cluster [default: zfs-cluster]: " cluster_name

	if [[ -z $cluster_name ]]
	then
	  pcs cluster setup --start --name $cluster_name $node1_hostname $node2_hostname
	else
	  pcs cluster setup --start --name zfs-cluster $node1_hostname $node2_hostname
	fi

	echo "Configuring cluster.."
	pcs property set no-quorum-policy=ignore
	pcs resource defaults resource-stickiness=100
	echo "Creating scsi fence device.."
	create_scsi_fence $node1_hostname $node2_hostname
#	create_devmapper_pool
	create_pool_resource
	create_floating_ip	
	create_pwr_fence $node1_hostname
	create_pwr_fence $node2_hostname
	pcs stonith level add 1 $node1_hostname scsi_fence
	pcs stonith level add 2 $node1_hostname ipmi_pwrfence_`echo $node1_hostname | sed 's/\./\_/g'`
	pcs stonith level add 1 $node2_hostname scsi_fence
        pcs stonith level add 2 $node2_hostname ipmi_pwrfence_`echo $node2_hostname | sed 's/\./\_/g'`
	echo "Creating Samba resource.."
	pcs resource create smbd_resource systemd:smb op start timeout=20 op stop timeout=20 op monitor interval=10 meta target-role=Started --group samba_group_resource
	pcs resource create winbind_resource systemd:winbind op start timeout=30 op stop timeout=20 op monitor interval=10 meta target-role=Started --group samba_group_resource
	echo "Creating NFS resource.."
	pcs resource create nfs_resource systemd:nfs op start interval=0 timeout=20 op stop interval=0 timeout=20 op monitor interval=10 meta target-role=Started 
        pcs constraint order set scsi_fence ipmi_pwrfence_`echo $node1_hostname | sed 's/\./\_/g'` ipmi_pwrfence_`echo $node2_hostname | sed 's/\./\_/g'` pool_resource nfs_resource samba_resource
	pcs constraint colocation add ipmi_pwrfence_`echo $node1_hostname | sed 's/\./\_/g'` with scsi_fence
	pcs constraint colocation add ipmi_pwrfence_`echo $node2_hostname | sed 's/\./\_/g'` with scsi_fence
	pcs constraint colocation add pool_resource with scsi_fence
	pcs constraint colocation add nfs_resource with pool_resource
	pcs constraint colocation add samba_group_resource with pool_resource
}

set_hostname(){
	echo
	read -p "\nEnter a hostname: " hostname
	if [[ $hostname == *['!'@#\$%^\&*()_+]* ]]
	then
	  echo "$hostname is not a valid hostname, please try again."
	  set_hostname
	fi
	echo 
	read -p "Are you sure you want set $hostname as hostname for this machine?(y/n)" input
	echo
	case $input in 
  	  (Y|y) hostnamectl set-hostname $hostname; echo "Configured hostname as $hostname";;
	  (N|n) echo "Lets try that again."; set_hostname;;
	esac
}

create_devmapper_pool(){
	echo	
}

create_scsi_fence(){
	systemctl restart multipathd
	mapper_entries=`ls /dev/mapper`
	for id in mapper_entries
	do
	  if [[ $id == 'control' ]]
	  then
	    continue
	  else
	    ids+="/dev/mapper/$i,"
	  fi
	done
	pcs stonith create scsi_fence fence_scsi pcmk_host_list="$1, $2" devices="$ids" meta provides=unfencing
}

create_pool_resource(){
	pools=`zpool list | awk '{print $1}' | sed '1d'`
	echo "Please select a pool to configure HA with."

	if [[ $pools == 'no'  ]]
	then
          echo "No pools found!"
          echo "Please create a pool and try again"
          exit
	else
          echo "Available ZFS pools:"
          echo $pools
	fi

	read -p "Enter Pool name: " pool
	pcs resource create pool_resource ZFS pool="$pool" importargs="-d /dev/mapper/" op start timeout="30" op stop timeout="30"

}

create_floating_ip(){
        echo "Configuring floating IP.."
        echo "Floating IP will be used by clients to access services"

        while true
        do
          read -p "Enter a IP address: " float_ip
          if [[ $float_ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]
          then
            break
          else
            echo "$float_ip is not a valid IP address. Please try again."
            continue
          fi
        done

        while true
        do
          read -p "Enter netmask address: " netmask
          if [[ $netmask =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]
          then
            prefix=`ipcalc -p $float_ip $netmask | cut -d '=' -f2`
            if [[ $prefix -gt 1 ]]
            then
              echo "pcs resource create float-ip IPaddr2 ip=$float_ip cidr_netmask=$prefix"
              break
            else
              echo "Unable to convert netmask to CIDR format, Please try again."
              continue
            fi
          else
              echo "$netmask is not valid, please try again."
              continue
          fi
        done
           
}

create_pwr_fence(){
        echo "configuring IPMI power fence for $1.."

        while true
        do
          while true
          do
            read -p "Please enter IPMI device IP for $1: " ipmi_ip
            if [[ $ipmi_ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]
            then
              break
            else
              echo "$ipmi_ip is not a valid IP address."
              continue
            fi
          done
  
          read -p "Enter IPMI username: " ipmi_user
          read -p "Enter IPMI password: " ipmi_pass
          check=`ipmitool -H $ipmi_ip -U $ipmi_user -P $ipmi_pass chassis power status`

          if [[ $? -eq 0 ]]
          then
            pcs stonith create ipmi_pwrfence_`echo $1 | sed 's/\./\_/g'` fence_ipmilan pcmk_host_list="$1" ipaddr="$ipmi_ip" login="$ipmi_user" passwd="$ipmi_pass" op monitor interval=30
            break
          else
            echo "IPMI details seem to be invalid, please try again."
            continue
          fi
        done

}


configure_nodes
