#!/usr/bin/env python2
import json
import socket
import operator
import time
import numpy as np
from strafe_controller import strafe_controller
import curses


class perplexity_controller(strafe_controller):
    def __init__(self, strafe_host="192.168.2.1", strafe_port=14550,
                 curses_screen=None, perplexity_host="localhost",
                 perplexity_port=9001, boredom_rate=0.999,
                 ptype="topic_perplexity", use_max=False,
                 strafe_gains=[5.0, 0.0, 0.0]):

        super(perplexity_controller, self).__init__(
            strafe_host, strafe_port, curses_screen)

        self.tcp_sock = None
        self.tcp_host = perplexity_host
        self.tcp_port = int(perplexity_port)

        self.kp = np.array([strafe_gains[0]], dtype=np.float64)
        self.ki = np.array([strafe_gains[1]], dtype=np.float64)
        self.kd = np.array([strafe_gains[2]], dtype=np.float64)

        self.previous_error = np.array([0], dtype=np.float64)
        self.integral_error = np.array([0], dtype=np.float64)
        self.curr_time = time.time()

        self.perplexity_threshold = 1.0
        self.boredom_rate = boredom_rate
        self.ptype = ptype
        self.use_max = use_max

        self.target_smoothing = 0.85

        self.prev_p_x = 0.0
        self.prev_p_y = 0.0

        self.connected = False

    def connect(self):
        # Connect to BlueROV
        super(perplexity_controller, self).connect_pymvalink()

        # Connect to ROST
        if self.tcp_sock is not None:
            self.disconnect()

        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.tcp_sock.settimeout(5.0)
        try:
            self.tcp_sock.connect((self.tcp_host, self.tcp_port))
            self.connected = True
            return True
        except socket.error:
            return False

    def disconnect(self):
        # Disconnect ROST 
        self.tcp_sock.close()
        self.tcp_sock = None
        # Disconnect to BlueROV
        super(perplexity_controller, self).disconnect_pymvalink()

    def get_max_perplexity_coords(self, perplexity_dict,
                                  ptype="topic_perplexity", image_width=640.0,
                                  image_height=480.0, hfov=90, vfov=90,
                                  normalized=False, smoothing=False):
        rows = int(perplexity_dict['rows'])
        cols = int(perplexity_dict['cols'])
        N = rows*cols
        cell_width = image_width/cols
        cell_height = image_height/rows

        # get the maximum
        max_ind = N/2
        max_val = 1.0
        if self.use_max:
            if ptype == "both":
                combined_perplexity = np.array(
                    perplexity_dict["topic_perplexity"])
                combined_perplexity *= np.array(
                    perplexity_dict["word_perplexity"])
                max_ind, max_val = max(
                    enumerate(combined_perplexity), key=operator.itemgetter(1))
            else:
                max_ind, max_val = max(
                    enumerate(perplexity_dict[ptype]),
                    key=operator.itemgetter(1))
        else:
            if ptype == "both":
                combined_perplexity = np.array(
                    perplexity_dict["topic_perplexity"])
                combined_perplexity *= np.array(
                    perplexity_dict["word_perplexity"])
                max_ind = np.random.choice(
                    N, 1, p=combined_perplexity/combined_perplexity.sum())[0]
                max_val = combined_perplexity[max_ind]
            else:
                perplexity_distribution = np.array(perplexity_dict[ptype])
                max_ind = np.random.choice(
                    N, 1,
                    p=perplexity_distribution/perplexity_distribution.sum())[0]
                max_val = perplexity_distribution[max_ind]

        # convert the index to cell corrdinates
        c_x = max_ind % cols + 0.5
        c_y = int(max_ind/cols) + 0.5

        # convert the cell coordinates to a pixel coordiinate vector centered
        # in the middle of the image
        p_x = c_x*cell_height - image_width/2.0
        p_y = -c_y*cell_width + image_height/2.0
        if normalized:
            p_x = p_x/(image_width/2.0)
            p_y = p_y/(image_height/2.0)

        if smoothing:
            alpha = self.target_smoothing
            p_x = (1-alpha)*self.prev_p_x + alpha*p_x
            p_y = (1-alpha)*self.prev_p_y + alpha*p_y
            self.prev_p_x = p_x
            self.prev_p_y = p_y

        return (p_x, p_y, max_val)

    def get_control(self, error):
        msg = "                                               "
        self.myscreen.addstr(18, 25, msg)
        if error < -100: 
            msg = "Nudging left: %f"
            self.myscreen.addstr(18, 25, msg % (error))
    	    self.send_strafe_command(1400)
            return 'L'
        elif error > 100: 
            msg = "Nudging right: %f"
            self.myscreen.addstr(18, 25, msg % (error))
	    self.send_strafe_command(1600)
            return 'R'
        else: 
            msg = "Staying in center: %f"
            self.myscreen.addstr(18, 25, msg % (error))
	    self.send_strafe_command(1500)
            return 'C'

        '''
        dt = time.time() - self.curr_time
        self.curr_time = time.time()
        de = error-self.previous_error
        self.previous_error = error
        #self.integral_error += error*dt
        self.integral_error = 0

        command = self.kp*error + self.ki*self.integral_error + self.kd*de/dt

        return command
        '''

    def run(self, strafe_init = 1500):
        infile = self.tcp_sock.makefile()

        self.myscreen.clear()
        self.myscreen.border(0)
        self.myscreen.addstr(6, 5, "Press 'q' to go back.")
        self.myscreen.nodelay(1)
        c = ''
        self.strafe = strafe_init 
        self.send_strafe_command(self.strafe)

        iters = 0

        while c != ord('q'):
            iters += 1
            self.myscreen.refresh()
            c = self.myscreen.getch()
            self.myscreen.addstr(
                12, 25, "Strafe: %f " % (self.strafe))
            if not self.connected:
                try:
                    self.tcp_sock.connect((self.tcp_host, self.tcp_port))
                    infile = self.tcp_sock.makefile()
                    self.connected = True
                    self.myscreen.addstr(
                        14, 25,
                        "Connected!                                    ")
                    time.sleep(1.0)
                    continue
                except socket.error as e:
                    self.myscreen.addstr(
                        14, 25,
                        "Lost connection, trying to reconnect...       ")
                    self.myscreen.addstr(
                        15, 25,
                        "                                               ")
                    self.myscreen.addstr(15, 25, str(e))
                    self.connected = False
                    time.sleep(1.0)
                    continue
            try:
                try:
                    line = infile.readline()

                    if not line:
                        self.connected = False
                        self.myscreen.addstr(
                            14, 25,
                            "Lost connection, trying to reconnect...       ")
                        self.myscreen.addstr(
                            15, 25,
                            "                                               ")
                        self.tcp_sock = socket.socket(
                            socket.AF_INET, socket.SOCK_STREAM)
                        # self.tcp_sock.settimeout(5.0)
                        time.sleep(1.0)
                        continue
                except socket.error as e:
                    self.connected = False
                    self.myscreen.addstr(
                        14, 25,
                        "Lost connection, trying to reconnect...       ")
                    self.myscreen.addstr(
                        15, 25,
                        "                                               ")
                    self.myscreen.addstr(15, 25, str(e))
                    self.tcp_sock = socket.socket(
                        socket.AF_INET, socket.SOCK_STREAM)
                    # self.tcp_sock.settimeout(5.0)
                    time.sleep(1.0)
                    continue

                result = json.loads(line)
                max_perplexity_px = self.get_max_perplexity_coords(
                    result, ptype=self.ptype)
                msg = "Current perplexity threshold: %f"
                self.myscreen.addstr(14, 25, msg % (self.perplexity_threshold))
                msg = "                                               "
                self.myscreen.addstr(15, 25, msg)

                msg = "Perplexity of target point: %f"
                self.myscreen.addstr(15, 25, msg % (max_perplexity_px[2]))
                msg = "                                               "
                self.myscreen.addstr(16, 25, msg)

                msg = "Max perplexity pixel loc: %s"
                self.myscreen.addstr(16, 25, msg % (str(max_perplexity_px[:2])))
                
                error = np.array(max_perplexity_px[:2])
                control = self.get_control(error[0])

                msg = "                                               "
                self.myscreen.addstr(17, 25, msg)
                msg = "Control: %s"
                self.myscreen.addstr(17, 25, msg % (str(control)))

                if max_perplexity_px[2] > self.perplexity_threshold:
                    self.perplexity_threshold = max_perplexity_px[2]
                    self.perplexity_threshold *= self.boredom_rate
                else:
                    self.perplexity_threshold *= self.boredom_rate
                    continue


            except ValueError:
                continue

            # the error is how far the max perxplexity coordinates are from
            # the center of the image
            #if max_perplexity_px[2] > self.perplexity_threshold:
            '''
            error = np.array(max_perplexity_px[:2])
            control = self.get_control(error[0])

            msg = "                                               "
            self.myscreen.addstr(17, 25, msg)
            msg = "Control: %s"
            self.myscreen.addstr(17, 25, msg % (str(control)))
            '''


        self.disconnect()
        self.disconnect_pymvalink()
        self.myscreen.clear()
        curses.flushinp()
        self.myscreen.nodelay(0)
        return (self.strafe)
