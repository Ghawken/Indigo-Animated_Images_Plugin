## Animated Images Control Page Plugin

Another fairly straight forward Plugin.

Spins up another built in Sanic app to manage animated gif's and webm images in Control pages/and in Indigo Touch.


Basically it adds animated images either Gifs or Webm to Pictures/Indigo-AnimatedImages, correct folder will be created on plugin startup.

Then Add URL to images via

http://127.0.0.1:8405/duck.gif

to Any control page as a refreshing URL.  This will be animated at the time frequency you set in the control page settings.

So:

## Simple Usage

Install

Defaults to port 8405

Check started correctly - Config Logging as wished.

Add animated gifs, or webms to /Pictures/Indigo-AnimatedImages -- all in one folder, as many as wished

Access these seperately via url which is http://127.0.0.1:8405/filenameofimage.filenameextension


Image exists: refresh_icon.gif placed within above directory

Enter: http://127.0.0.1:8405/refresh_icon.gif as refreshing URL in Control Page.  Animated Gif!

![refresh_icon.gif](Images%2Frefresh_icon.gif)
![Sunrise.gif](Images%2FSunrise.gif)
[Wow.webp](Images%2FWow.webp)

## Advanced Usage

Allows passing of control states via url, also allowing variable and device substitution.  Indigo standard substituion supported
https://wiki.indigodomo.com/doku.php?id=indigo_2023.2_documentation:plugins:variable_substitution

Now is the time to mention that also supports no animated images - such as all formats for display as below.

## Control Options

### 1. show=

show=true, or show=false
True Values:
"yes", "true","1", "yeah", "yep", "ok", "on","active","activated", "home", "100"
False Values:
Anything that is not above

Enables or displays display of image.  If false a blank, transparent image will be presented, very quickly and with very little overhead.
(as gets presented before even needs to read Gif image)

### **Allows substitution of both variable and device states.**
eg. Variable true/false, or device state On or Off

http://127.0.0.1:8405/duck.gif?show=%%v:12312123%%

Allows use of animated gif's depending on either device state or variable state.  Probably not this duck!

![duck.gif](Images%2Fduck.gif)

### 2. id=

Pass a Id variable for unique id purposes if using multiple same gif filenames in same page.

Otherwise without this and multiple same filenames all frames of every image would be same.  Id usage fixes this issue.

http://127.0.0.1:8405/duck.gif?id=123

http://127.0.0.1:8405/duck.gif?id=145

Enable 2 same gifs to be displayed, using same memory footprint but keeping frames seperate.

Compatible with combining Control options for example

http://127.0.0.1:8405/duck.gif?id=123&show=%%v:12312123%%

