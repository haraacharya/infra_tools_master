import serial
import time
import os
import subprocess
import re
import sys
import psutil

# port = "/dev/pts/16"



def isThisProcessRunning(process_name):
    ps = subprocess.Popen("ps -eaf | grep -w " + process_name + " | grep -v grep", shell=True, stdout=subprocess.PIPE)
    output = ps.stdout.read()
    # print (output)
    ps.stdout.close()
    ps.wait()

    if re.search(process_name, str(output)) is None:
        print("%s process not found" %(process_name))
        return False
    else:
        print("%s process found" % (process_name))
        return True

#base method to initialize the pyserial port
def initializePySerial(port = "/dev/pts/16"):
    ser = serial.Serial(
    port = port,
    baudrate = 115200,
    bytesize = serial.EIGHTBITS, 
    parity = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE, 
    timeout = 2,
    xonxoff = False,
    rtscts = False,
    dsrdtr = False,
    writeTimeout = 2
    )
    #for debug purpose
    if ser.isOpen():
        return ser
    else:
        return False
    
def getSerialDump(port = "/dev/pts/16"):
    ser = initializePySerial(port = port)
    if ser:
        time.sleep(1)
        ser.write("\r\n".encode())
        time.sleep(2)
        input_data = ser.read(ser.inWaiting())
        
        print (input_data)
        input_string = str(input_data).rstrip()
        # print (input_string)
        ser.close()             # close port
        return input_string
    else:
        print("port is not open")
        ser.close()             # close port
        return False   

def detectLoginPromptAndLogIn(port = "/dev/pts/16", waitForLoginPromptSeconds = 90):
    
    loginPrompt = False
    loggedInPrompt = False
    print ("waiting for %d seconds and keep checking for login prompt" % (waitForLoginPromptSeconds))
    for i in range(waitForLoginPromptSeconds):
        time.sleep(1)
        serialDump = getSerialDump(port = port)
        print("########################")
        print (serialDump)
        print("########################")
        if serialDump:
            #checking for already loggedin prompt
            logedInPattern = "localhost.*~.*#"
            if re.search(logedInPattern, serialDump):
                print("The console has already been logged. Exitin as True ")
                return True
            
            print ("Checking for login prompt*****")
            if 'localhost login:' in serialDump:
                print("localhost login prompt found")
                loginPrompt = True
                break
            else:
                print("localhost login prompt not found")
        else:
            print("port is not open")
            return False
    ser = initializePySerial(port = port)
    if loginPrompt:
        cmd="root\n"
        ser.write(cmd.encode())
        time.sleep(3)
        cmd = "test0000\n"
        ser.write(cmd.encode())
        
    serialDump = getSerialDump(port = port)
    # ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    # serialDump = ansi_escape.sub('', serialDump)
    print("---------------")
    print (serialDump)
    print("---------------")
    logedInPattern = "localhost.*~.*#"
    
    if re.search(logedInPattern, serialDump):
        print("login success")
        ser.close()             # close port
        return True
    else:
        print("Login not successfull")
        ser.close()             # close port
        return False
    
def detectLoggedinPrompt(port = "/dev/pts/16", waitForLoggedinPromptSeconds = 600):
    loggedInPrompt = False
    print ("keep checking for loggedin prompt for time taking command completion check")
    command_output = []
    for i in range(waitForLoggedinPromptSeconds):
        time.sleep(1)
        print("loggedin prompt check time remaining %d of %d seconds." %((waitForLoggedinPromptSeconds - i), waitForLoggedinPromptSeconds))
        serialDump = getSerialDump(port = port)
        print("########################")
        command_output.append(serialDump)
        print (serialDump)
        print("########################")
        if serialDump:
            logedInPattern = "localhost.*~.*#"
            if re.search(logedInPattern, serialDump):
                print("Got loggedin prompt. Exitin as True ")
                return (True, command_output)
    print("exceeded %d minutes waiting for loginprompt. returning false." %(waitForLoggedinPromptSeconds/60))
    return (False, command_output)

def ecResetOverSerial(port = "/dev/pts/16", cmd = "reboot\n"):
    ser = initializePySerial(port = port)
    ser.write(cmd.encode())
    time.sleep(2)
    ser.close()             # close port
    print ("ec reboot command executed")

    
def getCommandOutputOverSerial(port = "/dev/pts/16", cmd = "ip r s\n"):
    ser = initializePySerial(port = port)
    if detectLoginPromptAndLogIn(port = port):
        ser.write(cmd.encode())
        time.sleep(2)
        cmd_output_list = []
        while True:
            serial_line = ser.readline()
            serial_line_str = serial_line.decode()
            print(serial_line_str)
            cmd_output_list.append(serial_line_str.rstrip())
            if len(serial_line) == 0:
                break
        
        ser.close()             # close port
        return cmd_output_list
    else:
        print ("DUT serial not loggedin. DUT serial Login not attempt unsuccessful. Can't run command...")
        return False

def getTimeTakingCommandOutputOverSerial(port = "/dev/pts/16", cmd = "ip r s\n", string_to_match = ""):
    ser = initializePySerial(port = port)
    cmd_output_as_string = "" 
    if detectLoginPromptAndLogIn(port = port):
        ser.write(cmd.encode())
        time.sleep(2)
        # cmd_search_string_match = False
        #detect loggedin prompt and string match and within time limit
        result = detectLoggedinPrompt(port = port, waitForLoggedinPromptSeconds = 900)
        if result[0]:
            print("**********************************************************************************************")
            print(result[1])
            if len(string_to_match) >= 1: 
                cmd_output_as_string = ''.join(result[1])
                print(cmd_output_as_string)
                if re.search(string_to_match, cmd_output_as_string, re.IGNORECASE):
                    # cmd_search_string_match = True
                    print("**********************************************************************************************") 
                    print ("cmd_search_string_matched!!!!!")
                    print("%s command successful. Returning the cmd_output." % (cmd))
                    return cmd_output_as_string
                else:
                    print("%s command exited successfully but commandoutput check failed!!")
                    return False
            else:
                print("No command output string to be matched. Skipping command output string match step")
                return cmd_output_as_string

        #below while true logic doesn't work if console stops printing for some time for a command
        # while True:
        #     serial_line = ser.readline()
        #     serial_line_str = serial_line.decode()
        #     print(serial_line_str)
        #     serialDump = getSerialDump(port = port)
        #     cmd_output_list.append(serialDump)
        #     serialDump = getSerialDump(port = port)
        #     if len(serial_line) == 0:
        #         break
        else:
            print("%s didnt execute successfully as loggedin prompt not found after executing the command. Returning False" % (cmd))
            return False
    else:
        print ("DUT serial not loggedin. DUT serial Login not attempt unsuccessful. Can't run command...")
        return False

def getDutIp(port="/dev/pts/16"):
    ip_cmd_output_list = getCommandOutputOverSerial(port = port, cmd = "ip r s\n")        
    print ("*********************")
    if ip_cmd_output_list:
        print(ip_cmd_output_list)
        required_string = ""
        eth_pattern = "\s+eth"
        for item in ip_cmd_output_list:
            if re.search(eth_pattern,item):
                required_string = item
                break
        required_string = required_string.rstrip()
        dut_ip = required_string.split(" ")[-1]
        print("dut ip is: ", dut_ip)
        return dut_ip
    else:
        print("Unable to find dut ip. DUT IP check command failed.")
        return False

def getOsVersion(port = "/dev/pts/16"):
    os_version_cmd_output_list = getCommandOutputOverSerial(port = port, cmd = "cat /etc/lsb-release\n")
    print(os_version_cmd_output_list)
    if os_version_cmd_output_list:
        os_version_string = ""
        for item in os_version_cmd_output_list:
            if "CHROMEOS_RELEASE_BUILD_NUMBER" in item:
                os_version_string = item
                break
        os_version_string = os_version_string.rstrip()
        os_version = os_version_string.split("=")[-1]
        print("os version is: ", os_version)
        return os_version
    else:
        print("Unable to find os version. Os version command failed.")
        return False 

def cleanupMinicomCu():
    kill_minicom_cmd = "pgrep minicom | xargs sshpass -p intel123 sudo kill -9"
    kill_cu_cmd = "pgrep cu | xargs sshpass -p intel123 sudo kill -9"
    if isThisProcessRunning("minicom"):
        os.system(kill_minicom_cmd)
    if isThisProcessRunning("cu"):
        os.system(kill_cu_cmd)