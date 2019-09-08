from integralstor import command, networking
import os, socket, sys, re

def configure_cluster(nodes):
    try:
        print "Adding entries in hosts file.."
        ret, err = networking.update_hosts_file_entry(nodes['node1']['hostname'],
                                                        nodes['node1']['ip'])
        if err:
            raise Exception(err)
        ret, err = networking.update_hosts_file_entry(nodes['node2']['hostname'],
                                                        nodes['node2']['ip'])
        if err:
            raise Exception(err)
        print "Please make sure that the hosts file on the other node is also updated!"
        print "Authenticating cluster nodes.."
        ret, err = command.get_command_output("pcs cluster auth %s %s -u hacluster -p hacluster" %
                                                (nodes['node1']['hostname'],
                                                 nodes['node2']['hostname']))
        if err:
            raise Exception(err)
        if ret:
            print ret
        print "Setting up cluster.."
        ret, err = command.get_command_output("pcs cluster setup --start --name zfs-cluster %s %s" %
                                              (nodes['node1']['hostname'],
                                               nodes['node2']['hostname']))
        if err:
            raise Exception(err)
        if ret:
            print ret
        ret, err = command.get_command_output("pcs property set no-quorum-policy=ignore")
        if err:
            raise Exception(err)
        if ret:
            print ret
        ret, err = command.get_command_output("pcs resource defaults resource-stickiness=100")
        if err:
            raise Exception(err)
        if ret:
            print ret
    except Exception, e:
        print "Error configuring nodes: %s" % e

def create_scsi_fence():
    pass

def delete_scsi_fence():
    pass

def modify_scsi_fence():
    pass


def main():
    try:
        nodes = {}
        node1_hostname, err = networking.get_hostname()
        if err:
            raise Exception("Error getting hostname: %s" % err)
        print "HA Configuration requires hostname and IP address of the participating nodes"
        if not node1_hostname:
            print "Hostname not set, Please set a hostname for this machine before configuring HA"
            while True:
                node1_hostname = raw_input("Hostname: ")
                valid, err = networking.validate_hostname(node1_hostname)
                if err:
                    raise Exception("Error validating hostname: %s" % err)
                if err and not valid:
                    print "Invalid Hostname!"
                    continue
                if re.findall(r"\w+\.", node1_hostname):
                    tmp = node1_hostname.split('.')
                    ok, err = networking.update_hostname(tmp[0], "".join(tmp[1:]))
                else:
                    ok, err = networking.update_hostname(node1_hostname)
                if err:
                    raise Exception("Error updating hostname: %s" % err)
                if not ok:
                    print "Unable to update hostname!"
                else:
                    break
        else:
            print "Current Hostname for this machine is %s" % node1_hostname
            ch = raw_input("Do you want to change it? (y/n): ")
            if ch.lower() == "y" or ch.lower() == "yes":
                while True:
                    node1_hostname = raw_input("Hostname: ")
                    valid, err = networking.validate_hostname(node1_hostname)
                    if err:
                        raise Exception("Error validating hostname: %s" % err)
                    if not valid:
                        print "Invalid hostname!"
                        continue
                    if re.findall(r"\w+\.", node1_hostname):
                        tmp = node1_hostname.split('.')
                        ok, err = networking.update_hostname(tmp[0], "".join(tmp[1:]))
                    else:
                        ok, err = networking.update_hostname(node1_hostname)
                    if err:
                        raise Exception("Error updating hostname: %s" % err)
                    if not ok:
                        print "Unable to update hostname!"
                    else:
                        break
        print "HA Configuration requires the hostname to be resolvable by an IP address"
        while True:
            node1_ip = raw_input("Please enter IP for %s: " % node1_hostname)
            valid, err = networking.validate_ip(node1_ip)
            if err:
                raise Exception("Error validating IP address: %s" % err)
            if not valid:
                print "Invalid IP Adress!"
            else:
                connect, err = networking.can_ping(node1_ip)
                if err:
                    raise Exception("Error trying to ping host: %s " % err)
                if not connect:
                    print "%s is not reachable, Please check if you've entered the correct IP address" % node1_ip
                    continue
                break
        while True:
            node2_hostname = raw_input("Please enter second node's hostname: ")
            valid, err = networking.validate_hostname(node2_hostname)
            if err and not valid:
                print "Invalid hostname!"
            else:
                break
        while True:
            node2_ip = raw_input("Please enter IP for %s: " % node2_hostname)
            valid,  err = networking.validate_ip(node2_ip)
            if err:
                raise Exception("Error validating IP address: %s" % err)
            if not valid:
                print "Invalid IP Adress!"
            else:
                connect, err = networking.can_ping(node2_ip)
                if err:
                    raise Exception("Error trying to ping host: %s" % err)
                if not connect:
                    print "%s is not reachable, Please check if you've entered the correct IP address" % node2_ip
                    continue
                break
        nodes["node1"] = {'hostname': node1_hostname, 'ip': node1_ip}
        nodes["node2"] = {'hostname': node2_hostname, 'ip': node2_ip}
        configure_cluster(nodes)
    except Exception, e:
        print "Error configuring HA: %s" % e

if __name__ == "__main__":
    main()
