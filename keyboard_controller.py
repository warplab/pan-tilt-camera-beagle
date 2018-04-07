#!/usr/bin/env python2
import socket
import curses
from strafe_controller import strafe_controller	 
import time

class keyboard_controller(strafe_controller):
    def __init__(self, strafe_host= "192.168.2.1", strafe_port= 14550, curses_screen=None):
        super(keyboard_controller, self).__init__(strafe_host, strafe_port, curses_screen)

    def run(self, strafe_init=0.0):
        self.strafe = strafe_init 

        self.myscreen.clear()

        self.myscreen.border(0)
        #self.myscreen.addstr(3, 5, "Control tilt with UP/DOWN.")
        self.myscreen.addstr(4, 5, "Control strafe with LEFT/RIGHT.")
        #self.myscreen.addstr(5, 5, "Change step size with PG UP/PG DOWN.")
        self.myscreen.addstr(6, 5, "Press 'q' to go back.")
        c = ''

        while c != ord('q'):
            self.myscreen.addstr(12, 25, "Strafe: %f"%(self.strafe))
            #self.myscreen.addstr(13, 25, "Step size: %f"%(step))
            self.myscreen.refresh()
            c = self.myscreen.getch()
	    '''
            if c == curses.KEY_HOME:
                self.pan = tilt = 90.0
            elif c == curses.KEY_UP:
                self.tilt += self.tilt_speed
		if self.tilt > self.tilt_limits[1]:
		    self.tilt = self.tilt_limits[1] - 2
            elif c == curses.KEY_DOWN:
                self.tilt -= self.tilt_speed
		if self.tilt < self.tilt_limits[0]:
		    self.tilt = self.tilt_limits[0] + 2
	    '''
            if c == curses.KEY_LEFT:
		self.send_strafe_command(1400)
            elif c == curses.KEY_RIGHT:
		self.send_strafe_command(1600)
	    '''
            elif c == curses.KEY_NPAGE:
                self.pan_speed -= 0.1
                self.tilt_speed -= 0.1
                if self.pan_speed > 10.0:
                    self.pan_speed = 10.0
                    self.tilt_speed = 10.0
            elif c == curses.KEY_PPAGE:
                self.pan_speed += 0.1
                self.tilt_speed += 0.1
                if self.pan_speed < 0.1:
                    self.pan_speed = 0.1
                    self.tilt_speed = 0.1
            elif c == ord('r'):
                self.pan=90.0
                self.tilt=90.0
                self.pan_speed=1.0
                self.tilt_speed=1.0
	    '''
            #self.send_strafe_command(self.strafe)

        self.disconnect_pymvalink()
        self.myscreen.clear()
        return (self.strafe)
