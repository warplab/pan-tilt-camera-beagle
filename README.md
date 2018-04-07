# Strafe controller for the BlueROV
strafe_controller_client.py is used to send motor commands to the BlueROV2, either based on keyboard commands or the computed maximum perplexity pixel in a ROST image stream

perplexity_controller.py listens to perplexity json messages over a tcp socket and sends commands to the BlueROV (using rost-cli)

## Example
First, start an MJPEG image stream on the BlueROV, output to port 8080:
  
  ```./mjpg_streamer -i "input_raspicam.so -x 640 -y 480 -fps 15" -o "output_http.so -p 8080" ``` or
   ```./mjpg_streamer -i "input_uvc.so -d /dev/video0 -x 640 -y 480 -fps 15" -o "output_http.so -p 8080" ```

Then, compile rost-cli and run sunshine:
    
    cd <PATH_TO_ROST_CLI>/bin
    ./sunshine --mjpgstream=192.168.2.2 --mjpgstream.port=8080 --mjpgstream.path='/?action=stream' --hdp -K 32 --header=" " --footer=" " --broadcaster.port=9001 --cell.space=32

Then, run the perplexity controller:

    cd <PATH_TO_THIS_REPO>
    ./strafe_controller_client.py

Run `./strafe_controller_client --help` for a description of the arguments.


