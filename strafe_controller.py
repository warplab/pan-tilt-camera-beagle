#!/usr/bin/env python2
from pymavlink import mavutil
import socket
import curses
import time


class strafe_controller(object):
    '''
        simple PID controller for strafe BlueROV2
    '''
    def __init__(self, strafe_host= "192.168.2.1", strafe_port=14550,
                 curses_screen=None):

        self.udp_sock = None

        self.udp_host = strafe_host
        self.udp_port = int(strafe_port)

        self.strafe= 0.0

        self.strafe_speed = 1

        if curses_screen is None:
            self.myscreen = curses.initscr()
            self.myscreen.keypad(1)
            curses.noecho()
            curses.cbreak()
            self.myscreen.border(0)
        else:
            self.myscreen = curses_screen

    # Connect to mavlink via UDP
    def connect_pymvalink(self):
	print "Connecting to vechile at:", 'udp:' + self.udp_host + ':' + str(self.udp_port)
        self.master = mavutil.mavlink_connection('udp:' + self.udp_host + ':' + str(self.udp_port))
        self.master.wait_heartbeat()

	# Arm
	self.master.mav.command_long_send(
	    self.master.target_system,
	    self.master.target_component,
	    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
	    0,
	    1, 0, 0, 0, 0, 0, 0)

	# Choose a mode
	mode = 'ALT_HOLD'
	#mode = 'MANUAL'

	# Check if mode is available
	if mode not in self.master.mode_mapping():
	    print('Unknown mode : {}'.format(mode))
	    print('Try:', list(self.master.mode_mapping().keys()))
	    exit(1)

	# Get mode ID
	mode_id = self.master.mode_mapping()[mode]

	# Set new mode
	self.master.mav.set_mode_send(
	    self.master.target_system,
	    mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
	    mode_id)

	# Check ACK
	ack = False
	while not ack:
	    # Wait for ACK command
	    ack_msg = self.master.recv_match(type='COMMAND_ACK', blocking=True)
	    ack_msg = ack_msg.to_dict()

	    # Check if command in the same in `set_mode`
	    if ack_msg['command'] != mavutil.mavlink.MAVLINK_MSG_ID_SET_MODE:
		continue

	    # Print the ACK result !
	    print(mavutil.mavlink.enums['MAV_RESULT'][ack_msg['result']].description)
	    break

    def disconnect_pymvalink(self):
	# Disarm
	# master.arducopter_disarm() or:
	self.master.mav.command_long_send(
	    self.master.target_system,
	    self.master.target_component,
	    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
	    0,
	    0, 0, 0, 0, 0, 0, 0)

    # Create a function to send RC values
    # More information about Joystick channels
    # here: https://www.ardusub.com/operators-manual/rc-input-and-output.html#rc-inputs
    def set_rc_channel_pwm(self, id, pwm=1500):
	""" Set RC channel pwm value
	Args:
	    id (TYPE): Channel ID
	    pwm (int, optional): Channel pwm value 1100-1900
	"""
	if id < 1:
	    print("Channel does not exist.")
	    return

	# We only have 8 channels
	#http://mavlink.org/messages/common#RC_CHANNELS_OVERRIDE
	if id < 9:
	    rc_channel_values = [65535 for _ in range(8)]
	    rc_channel_values[id - 1] = pwm
	    self.master.mav.rc_channels_override_send(
		self.master.target_system,                # target_system
		self.master.target_component,             # target_component
		*rc_channel_values)                  # RC channel list, in microseconds.

    def connect(self):
        if self.udp_sock is not None:
            self.disconnect()
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.connect((self.udp_host, self.udp_port))

    def disconnect(self):
        self.udp_sock.close()
        self.udp_sock = None

    # This is where the pan and tilt command is actually sent
    # Should be changed to communicated over MAVLINK
    def send_strafe_command(self, strafe):
        self.strafe = strafe 

	if int(strafe) > 1600 or int(strafe) < 1400:
	    print "Invalid strafe: ", int(strafe), "! \r\n"
	    print "Strafe must be between 1400 and 1600 \r\n"
	    return False
    
	#print "Sending Strafe command", int(strafe), "\r\n"
	for i in xrange(10):
	    self.set_rc_channel_pwm(6, int(strafe))
	    #self.set_rc_channel_pwm(6, 1500)
	    time.sleep(0.02)

	return False
	'''
        msg = str(pan)+','+str(tilt)
        try:
            b = self.udp_sock.sendto(msg, (self.udp_host, self.udp_port))
            if b == len(msg):
                return True
        except socket.error:
            return False

        return False
	'''

    def run(self, strafe_init):
        pass
