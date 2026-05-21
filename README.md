# Traccar-Suckless
!YOU NEED IP OF YOUR TAILSCALE PC, NOT PHYSICAL (if isn't general network)!

This is Traccar. But way easier. 

I don't like traccar, this is shit, so I wrote my Traccar.

Why Traccar Suckless?

Existing solutions like Traccar are redundant:

the official installer weighs ~200 MB for Linux, requires a monolithic Java runtime environment and is tightly tied to systemd.
My project is a suckless alternative: it weighs ~2 MB, runs with a single command on any init system, and does exactly what a tracker is supposed to do — collect and display coordinates without unnecessary garbage, my phone just can't stand up with traccar, which is why it exists.
(IMHO traccar overloaded.)

Right now it is in development, has an apk file and a station in Python to keep an eye on the phone. If project will be have any popularity, then I will made support of many other OS, not only android.

How to launch this?

1. You should download traccar.apk (in releases) on the phone, and server.py (in releases) on the computer 

2. Connect your phone and computer to general tailscale account (or local network)

3. Check your PC IP in tailscale and enter in traccar suckless on phone. Use general port to connect.

4. Download python, download requirements (download from source files) with "pip install requirements.txt", launch server with command "python server.py". Enter general port.

5. Click on the phone "Start tracker" and wait until he finds satellite of GPS (around 1-3 mins). Done! Now you can watch for location of your phone.

Why so long?

Because of methods of searching, google cheating in this method: asks for location nearly located networks. TS searching for satellite and asks him for location.
