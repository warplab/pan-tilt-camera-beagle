#!/usr/bin/env python
import argparse
import atexit
import curses
import numpy as np
import traceback

from keyboard_controller import keyboard_controller
from perplexity_controller import perplexity_controller


def exit():
    curses.nocbreak()
    curses.echo()
    curses.endwin()

def main_loop(args):
    # Intitalize pan and tilt
    strafe = 1500
    pan = args.pan
    if args.pan is None:
        pan = np.random.uniform(args.pan_min, args.tilt_max)
    tilt = args.tilt
    if args.tilt is None:
        tilt = np.random.uniform(args.tilt_min, args.tilt_max)

    p_gains = [args.pan_kp, args.pan_ki, args.pan_kd]
    t_gains = [args.tilt_kp, args.tilt_ki, args.tilt_kd]

    use_max = (args.switching_mode == 0)

    k_controller = keyboard_controller(
        args.pt_host, args.pt_port, myscreen)

    tp_controller = perplexity_controller(
        args.pt_host, args.pt_port, myscreen, args.sunshine_host,
        args.sunshine_port, args.decay_rate, "topic_perplexity", use_max,
        strafe_gains=t_gains)

    wp_controller = perplexity_controller(
        args.pt_host, args.pt_port, myscreen, args.sunshine_host,
        args.sunshine_port, args.decay_rate, "word_perplexity", use_max,
        strafe_gains=t_gains)

    mp_controller = perplexity_controller(
        args.pt_host, args.pt_port, myscreen, args.sunshine_host,
        args.sunshine_port, args.decay_rate, "both", use_max,
        strafe_gains=t_gains)

    c = ord('k')
    while c != ord('q'):
        if c == ord('k'):
            k_controller.connect_pymvalink()
            (strafe) = k_controller.run(strafe)
        elif c == ord('t'):
            tp_controller.connect()
            (strafe) = tp_controller.run(strafe)
        elif c == ord('w'):
            wp_controller.connect()
            (strafe) = wp_controller.run(strafe)
        elif c == ord('m'):
            mp_controller.connect()
            (strafe) = mp_controller.run(strafe)

        myscreen.refresh()
        myscreen.addstr(3, 5, "Press 'k' for keyboard control")
        myscreen.addstr(4, 5, "Press 't' for topic perplexity control")
        myscreen.addstr(5, 5, "Press 'w' for word perplexity control")
        myscreen.addstr(6, 5, "Press 'm' for topic+word perplexity control")
        myscreen.addstr(7, 5, "Press 'q' to exit. %s" % args.decay_rate)
        myscreen.border(0)

        c = myscreen.getch()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A UDP client for controlling BlueROV strafe, either from keyboard input or a set of autonomous controllers")

    parser.add_argument('--pt_host', help="the hostname or ip or address of the pan tilt controller", type=str, default='192.168.2.1')
    parser.add_argument('--pt_port', help="the UDP port number of the pan tilt controller", type=int, default=14550)
    parser.add_argument('--sunshine_host', help="the hostname or ip address of the perplexity stream", type=str, default='localhost')
    parser.add_argument('--sunshine_port', help="the TCP port number of the perplexity stream", type=int, default=9001)
    parser.add_argument('--decay_rate', help="the decay rate for the perplexity threshold", type=float, default=0.999)

    parser.add_argument('--pan', help="initial pan angle", type=float, default=None)
    parser.add_argument('--tilt', help="initial pan angle", type=float, default=None)
    parser.add_argument('--pan_min', help="minimum pan limit", type=float, default=5)
    parser.add_argument('--pan_max', help="maximum pan limit", type=float, default=175)
    parser.add_argument('--tilt_min', help="minimum pan limit", type=float, default=5)
    parser.add_argument('--tilt_max', help="maximum pan limit", type=float, default=175)

    parser.add_argument('--tilt_kp', help="Proportional controller gain for panning", type=float, default=5.0)
    parser.add_argument('--pan_kp', help="Proportional controller gain for tilting", type=float, default=-1.0)
    parser.add_argument('--tilt_ki', help="Integral controller gain for panning", type=float, default=0.0)
    parser.add_argument('--pan_ki', help="Integral controller gain for tilting", type=float, default=-0.0)
    parser.add_argument('--tilt_kd', help="Derivative controller gain for panning", type=float, default=0.0)
    parser.add_argument('--pan_kd', help="Derivative controller gain for tilting", type=float, default=-0.0)

    parser.add_argument('--switching_mode', help="switching mode for the perplexity controller. 0: point camera to max perplexity, 1: draw target from perplexity distribution", type=int, default=0)

    args = parser.parse_args()

    atexit.register(exit)

    myscreen = curses.initscr()
    myscreen.keypad(1)
    curses.noecho()
    curses.cbreak()
    try:
        main_loop(args)
    except Exception as e:
        myscreen.keypad(0)
        exit()
        traceback.print_exc()
