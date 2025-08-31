# TALKING SERVER

Here's a simple way to add spoken audio to your klipper printer macros.

You'll need a raspberry pi to run the piper text-to-speech module. This could be your printers klipper CPU. This shouldn't affect the CPU load for printing, since usually you'll only need audio prompts when nothing is actually being printed (print starts, and error, print paused, load-more-filament, print-completed etc.).

## Add speakers

Either use the headphone jack of the PI or an audio tophat and some small speakers, and check audio works on the PI 

I've added two small speakers (and a speaker pi-hat I had spare)...

The speakers were simply hot glued in place...

![Components](../photos/PI.JPG)
![Components](../photos/SP1.JPG)
![Components](../photos/SP2.JPG)

## Install piper 

Text to Speech is achieved using piper (see this video 
[link](https://www.youtube.com/watch?v=rjq5eZoWWSo_) )
 - although the installation method has changed somewhat since the video was made.
 
 Here's the location of piper [link](https://github.com/OHF-Voice/piper1-gpl)
 
 In short, the install command is
 ```
 pip install piper-tts  --break-system-packages
 ```
 
 (Test without the break-system-packages option first, to see if it's required on your installation).
 
 You can then add the speak dialect you'd like to use - using the instruction at 
 [link](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/CLI.md) - there's dozens of voices / languages to choose from.
 
 Here's an example of loading the Voice en_GB-southern_english_female-low
```
 python3 -m piper.download_voices en_GB-southern_english_female-low
```


 
 ### Audio pi hat
 
 To get my audio amplifier working I had to do the following (thanks chatgpt)...

Edit /boot/config.txt and add the line:
```
   dtoverlay=audremap,pins_18_19
```
and reboot

## Install this simple script

Copy the file ttserver.py from the talkingserver folder to your pi (I copied it into my home folder).

#### Change voice used in the script

If you choose to load a different voice (from en_GB-southern_english_female-low), then you will need to edit the ttserver.py file as follows

Edit ttserver.py and replace the language in line number 20 (for example to  en_GB-cori-high)

```
        "-m", "en_GB-southern_english_female-low",
```  




### Test the talkingserver

You can run the server manually to test by running this command from your PI:

- python3 ttsserver.py

This will start the server. You can then call the server from a web browser using a call of this format:

- http://ADDRESSOFYOURPI:4601/?text="Words%20to%20be%20spoken"

or from the PI itself using

```
curl "http://ADDRESSOFYOURPI:4601/?text=Hello%20world"
```

If you want the text to be repeated (unit the next time you call the server), add a ':' to the start of the text.

```
curl "http://ADDRESSOFYOURPI:4601/?text=This%20will%20repeat"
```

You can then pass an empty string (or anything else) to stop the text being spoken.

```
curl "http://ADDRESSOFYOURPI:4601/?text=%20"
```

You can also put any audio file on the server, and just get it to play it using a '>' in the text to indicat that this is a filename - thus...

```
curl "http://ADDRESSOFYOURPI:4601/?text=>filenametoplay.wav"
```

## Get the server to run as a service (on startup)

The most reliable way to make the script start on boot on a Raspberry Pi is to set it up as a systemd service.
That way, it will automatically run in the background after every reboot, and restart if it crashes.

Here’s how to do it:

```
sudo nano /etc/systemd/system/ttsserver.service
```

Paste this:
```
[Unit]
Description=Text-to-Speech Web Server
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/ttsserver.py
WorkingDirectory=/home/pi
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Enable and start the service

```
sudo systemctl daemon-reload
sudo systemctl enable ttsserver.service
sudo systemctl start ttsserver.service
```

Check the status

```
sudo systemctl status tts_server.service
```

View logs if needed
```
journalctl -u ttsserver.service -f
```


## SAY - klipper macro to speak text.

Here's my gcode implementing the 'say'.

Paste this code into your config folder in a file called 'say.cfg', and ensure your printer.cfg includes this file.

```
[gcode_macro SAY]
description: Send text to remote TTS server

# --- CONFIGURABLE VARIABLES ---
variable_tts_host: "172.0.0.1"      # Change this to your TTS server IP/hostname
variable_tts_port: 4601             # Change this if you use a different port
# --------------------------------

gcode:
    {% set s = params.S|default("") %}
    {% if s == "" %}
        {action_respond_info("Usage: SAY S=\"your text here\"")}
    {% else %}
        {% set host = printer["gcode_macro SAY"].tts_host %}
        {% set port = printer["gcode_macro SAY"].tts_port %}
        {% set url  = "http://" ~ host ~ ":" ~ (port|string) %}
        {% set parms  = "--data-urlencode text=\'" ~ s ~ "\'" %}
        RUN_SHELL_COMMAND CMD="RUNSAY" PARAMS="{ parms } { url }"
    {% endif %}


[gcode_shell_command RUNSAY]
command: bash -c "curl -sG \"$0\" \"$1\" \"$2\""
timeout: 90.0
verbose: True

```

Now you can 'say' whatever you want from within your klipper macros...

### Speak a string

SAY S="PRINT HAS FINISHED"

### Repeat a string (2 second pause between each speech)

SAY S=">PAUSED - PLEASE LOAD FILAMENT"

### End a repeating speech

SAY S=" "   (Or any other SAY command)

### play a file

SAY S=">/home/sv08/FINISHED.wav"



