# sudo killall vino-server
# pgrep vnc | xargs kill -9
# pgrep tmux | xargs kill -9


# sudo apt-get remove vino
# sudo apt-get install tmux
# sudo apt-get install x11vnc

# pgrep vnc | xargs sudo kill -9
# pgrep tmux | xargs sudo kill -9
# tmux new-session -d -s vnc 'x11vnc --forever --shared --noxrecord --ncache_cr'
# sleep(15)
# if pgrep vnc true
# return true
# else
# check autologin enabled else enable autologin
# sudo reboot
# wait for system to be up...keep checking for 80 seconds
# 	sudo killall vino-server
# 	tmux new-session -d -s vnc 'x11vnc --forever -display 0 --shared --noxrecord --ncache_cr'
# 	sleep(15)
# 	if pgrep vnc true
# 	return true
# 	else
# 	return there is some problem and not able to start vnc
# else
# 	return system didnt come up after reboot

import paramiko
import os
import time
import argparse
import sys
from datetime import datetime
import logging
import logging.handlers


debug_log_folder = os.getcwd() + "/debug_log"
if not os.path.exists(debug_log_folder):
    os.makedirs(debug_log_folder)

log_file_name = debug_log_folder + "/" + datetime.now().strftime('%Y-%m-%d_%H-%M-%S') +"debug.log"

logging.basicConfig(filename= log_file_name, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger("paramiko").setLevel(logging.WARNING)
handler = logging.StreamHandler(sys.stdout)
dlogger = logging.getLogger(__name__)
dlogger.addHandler(handler)


def check_if_remote_system_is_live(ip):
    hostname = ip
    # print ("hostname is", hostname)
    try:
        response = os.system("ping -c 1 " + hostname + '>/dev/null 2>&1')
    except:
        return False

    if response == 0:
        return True
    else:
        return False

def runRemoteCommandSuccess(host, port = 22, username = "cssdesk", password = "intel123", command = "hostname"):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port, username, password)

    stdin, stdout, stderr = client.exec_command(command)
    dlogger.info(stdout.read())
    # for line in iter(stdout.readline, ""):
    #     print(line, end="")
    
    dlogger.info(stdout.channel.recv_exit_status()) 
    if stdout.channel.recv_exit_status() == 0:
        return True
    else:
        return False

#always use option -k to force ask the sudoer password
def runSudoCommandSuccess(host, port = 22, username = "cssdesk", password = "intel123", command = "hostname"):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port, username, password)    
    transport = ssh.get_transport()
    session = transport.open_session()
    session.set_combine_stderr(True)
    session.get_pty()
    session.exec_command(command)
    stdin = session.makefile('wb', -1)
    stdout = session.makefile('rb', -1) 
    stdin.write(password +'\n')
    stdin.flush()
    #list = print (type(stdout.readlines()))
    #class <bytes> = print (type(stdout.read()))
    # print(stdout.readlines())
    # for line in stdout.read().splitlines():        
    #     print ('host: %s: %s' % (host, line))
    if stdout.channel.recv_exit_status() == 0:
        return True
    else:
        return False


def reboot_remote_host(host, port = 22, username = "cssdesk", password = "intel123"):
    # client = paramiko.SSHClient()
    # client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # client.connect(host, port, username, password)

    reboot_wait_time = 120
    wait_device_initialization = 15
    # timeout=0.5
    # transport = client.get_transport()
    # chan = client.get_transport().open_session(timeout=timeout)
    # chan.settimeout(timeout)
    # try:
    #     chan.exec_command("/sbin/shutdown -r now")
    # except socket.timeout:
    #     pass
    runSudoCommandSuccess(host, username = username, password = password, command = "sudo -k /sbin/shutdown -r now > /dev/null 2>&1")
    time.sleep(5)
    if not check_if_remote_system_is_live(host):
        for i in range(reboot_wait_time):
                time.sleep(1)
                if check_if_remote_system_is_live(host):
                    print ("Waiting for system to boot up completely: ", wait_device_initialization)
                    time.sleep(wait_device_initialization)
                    return True
        dlogger.info ("system didn't reboot back on after %d seconds wait delay" % (reboot_wait_time))
        return False
    else:
        dlogger.info ("reboot command was not successful.")
        return False
    

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', dest='ip_address', help='provide remote system ip')
    parser.add_argument('--username', dest='username', default = "cssdesk", help='provide username if otherthan cssdesk!')
    parser.add_argument('--password', dest='password', default = "intel123", help='Provide password if otherthan intel123!')

    args = parser.parse_args()

    #taking care of argparse
    if args.ip_address:
        ip_address = args.ip_address
    else:
        ip_address = False
        dlogger.info ("check with --help or give cmd argument --ip <ip_address>")
        sys.exit(1)

    username = args.username
    password = args.password
    print(username)
    print(password)
    

    #sudo commands to clean up and install if not already installed
    sudo_fix_broken_install_command = "sudo apt --fix-broken install"
    sudo_remove_vino_command = "sudo -k apt-get remove vino -y"
    sudo_install_tmux_command = "sudo -k apt-get install tmux -y"
    sudo_install_x11vnc_command = "sudo -k apt-get install x11vnc -y"
    sudo_kill_vnc_command = "pgrep vnc | sudo -k xargs kill -9"
    sudo_kill_tmux_command = "pgrep tmux | sudo -k xargs kill -9"
    sudo_kill_gnome_remote_command = "pgrep gnome-remote | sudo -k xargs kill -9"
    sudo_disable_firewall_command = "sudo ufw disable"

    tmux_vnc_command = 'tmux new-session -d -s vnc "x11vnc -xkb -skip_keycodes 187,188 --forever --shared --noxrecord --ncache_cr"'
    # print(tmux_vnc_command)
    tmux_vnc_command_with_display_1 = 'tmux new-session -d -s vnc "x11vnc -xkb -skip_keycodes 187,188 --forever -display :1 --shared --noxrecord --ncache_cr"'

    runSudoCommandSuccess(ip_address, username = username, password = password, command = sudo_kill_vnc_command)
    runSudoCommandSuccess(ip_address, username = username, password = password, command = sudo_kill_tmux_command)
    runSudoCommandSuccess(ip_address, username = username, password = password, command = sudo_remove_vino_command)
    runSudoCommandSuccess(ip_address, username = username, password = password, command = sudo_kill_gnome_remote_command)
    runSudoCommandSuccess(ip_address, username = username, password = password, command = sudo_disable_firewall_command)
    
    if not runRemoteCommandSuccess(ip_address, username = username, password = password, command = "which tmux"):
        dlogger.info ("tmux not installed. Installing it")
        runSudoCommandSuccess(ip_address, username = username, password = password, command = sudo_fix_broken_install_command)
        runSudoCommandSuccess(ip_address, username = username, password = password, command = sudo_install_tmux_command)
    if not runRemoteCommandSuccess(ip_address, username = username, password = password, command = "which x11vnc"):
        dlogger.info ("x11vnc not installed. Installing it")
        runSudoCommandSuccess(ip_address, username = username, password = password, command = sudo_fix_broken_install_command)
        runSudoCommandSuccess(ip_address, username = username, password = password, command = sudo_install_x11vnc_command)

    
    if runRemoteCommandSuccess(ip_address, username = username, password = password, command = tmux_vnc_command):
        dlogger.info("waiting for 20 seconds to check if vnc started and running successfully else will try with display :1")
        time.sleep(20)
        if runRemoteCommandSuccess(ip_address, username = username, password = password, command = "pgrep vnc"):
            dlogger.info ("vnc running successfully")
        else:
            dlogger.debug("VNC is not running. Will try display :1")
            if runRemoteCommandSuccess(ip_address, username = username, password = password, command = tmux_vnc_command_with_display_1):
                dlogger.info("waiting for 20 seconds with display :1")
                time.sleep(20)
                if not runRemoteCommandSuccess(ip_address, username = username, password = password, command = "pgrep vnc"):
                    dlogger.info("Something wrong! can't be fixed using fixvnc script.")
                else:
                    dlogger.info("vnc fixed. Please check vnc on: %s" %(ip_address))
    else:
        dlogger.info("Something is wrong! Can't be fixed using fix_vnc script. It might need a reboot or Somebody has to lokinto the system physically.")