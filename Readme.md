# AESTube n' Wav
This is a PoC using youtube audio to encrypt text/files. It uses AES-256.
How it's done:
1. Download MP4 audio stream from a YouTube link.
2. MP4 audio is converted to WAV.
3. WAV is processed through FFT to extract audio frequencies.
4. Frequencies are mapped to musical notes.
5. These notes are used as the passphrase for AES encryption.
6. That's all folks 😎

In addition to this, nicomda created some audio splitting mechanism that allows you to trim it, improving the security.
## Installation (Read carefully. Some tweaks are needed)

## Required programs
1. ffmpeg
2. libsound portaudio19
3. pyaudio
Possibly youtube-dl as well. The requirements.txt should salsify that dependency but if you get issues with youtube-dl install the distro version.

Assure that you have python3 installed on your system.
```sh
#Clone this repo
git clone https://github.com/simmons2714/AESTube.git

#Install if not installed
pip3 install virtualenv

#Creating virtualenv
python3 -m venv AESTube

#Activating venv
source ./bin/activate

#Installing required libraries in the virtual enviroment (FFMpeg, pyaudio...)
cd AESTube
pip3 install -r requirements.txt

I removed the usage of pytube for youtube-dl and ffmpeg so this step should not be needed. Frankly, the way I used youtube-dl is nearly the same as nicomda but in one combined function. Plus I simp for youtube-dl. ¯\_(ツ)_/¯

~~~ Must update pytube as shown to get it working~~~
~~~ pip3 install git+https://github.com/nficano/pytube.git --upgrade~~~

```
## Quick Start
```bash
#To encrypt text: 
./AESTube.py -e -t 'text_to_encrypt' -s -l 'YoutubeLink' --start_time='HH:MM:SS' --end_time='HH:MM:SS'

#To decrypt files: 
./AESTube.py -e -d 'text_to_encrypt' -s -l 'YoutubeLink' --start_time='HH:MM:SS' --end_time='HH:MM:SS'
```

### **Available arguments:**

| Argument        | What it does | Optional |
| --------------- |:-------------|:---------:| 
| -e                               |Encrypt mode | 
| -d                               |Decrypt mode
| -t                               |String data
| -f <file_to_encrypt>             |File to encrypt
| -l, --yt_link= 'Youtube link'    |Audio that will be used to get passphrase
| -s                               |Splitted mode. Will get just a part of the audio. If used, you must set start_time and end_time args |✔
| -w                               |Local files
| --start_time=                    |Start of the split in seconds |✔
| --end_time=                      |Start of the split in seconds |✔

