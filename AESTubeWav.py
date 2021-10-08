#!bin/python3
#Notice that is venv enabled
from __future__ import unicode_literals
import youtube_dl
import numpy as np
import pyaudio
import wave
from pydub import AudioSegment
import struct
import math
import os, sys, glob, getopt
import hashlib
import subprocess
import base64
from requests import exceptions
from AESCipher import AESCipher


fs= 44100               #Sample Hz
scales = 8              #Amount of musical scales to work with (12 semitones)
duration = 0            #Audio duration in ms to control splitting
detected_notes = []     #Array to store detected notes
detected_freqs = []     #Array to store detected frequencies
ytLink = file_name = localfile = opData = opMode = opType = opSource = key = ''
isSplitted = isInvalid = isVerbose = False
startTime = endTime = ''

def getArgsOptions():
    global opMode, opType, opData, opSource, isSplitted, isVerbose, startTime, endTime, ytLink, localfile
    if len(sys.argv) == 1:
        printQuickHelp()
        sys.exit()
    argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argv, 'hedf:t:svw:l:', ["help","start_time=", "end_time=", "yt_link="])
    except getopt.GetoptError:
        print('Arguments error, just use as below or -h for more options.')
        printQuickHelp()
        sys.exit()
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            printExtendedHelp()
            sys.exit()
        elif opt == '-e':            
            opMode = 'E'  
        elif opt== '-d':
            opMode = 'D'
        elif opt in ('-f'):
            opType = 'F' 
            opData =  arg
        elif opt in '-t':
            opType = 'T'
            opData = arg
        elif opt == '-s':
            isSplitted = True
        elif opt == '-v':
            isVerbose = True
        elif opt in ('-l', '--yt_link'):
            opSource = 'L'
            ytLink = arg
        elif opt in ('-w'):
            opSource = 'W'
            localfile = arg
        elif opt in ('--start_time'):
            startTime = arg
        elif opt in ('--end_time'):
            endTime = arg

def printExtendedHelp():
    print('Available arguments')
    print('-e                               Encrypt mode')
    print('-d                               Decrypt mode')
    print('-t                               String data')
    print('-f <file_to_encrypt>             File to encrypt')
    print("-l, --yt_link= 'Youtube link'    Audio that will be used to get passphrase")
    print("-w              'Local File'     Local audo that will be use to get passphrase")
    print('-s                               Splitted mode. It will get just a part of the audio. If you use it, you must set start_time and end_time args')
    print('--start_time=                    Start of the split in seconds')
    print('--end_time=                      Start of the split in seconds')
    print('Split uses the ffmpeg flag -to')
    print("Local files have to be wav. Use ffmpeg -y -i '<input file.extension>' -ab 96k -ac 1 -ar 44100 -vn '<output file name>.wav' to fix it")
    printQuickHelp()

def printQuickHelp():
    print("***Quick Usage steps***")
    print("--------------------YouTube and Cli Strings--------------------")
    print("To encrypt text: AESTube.py -e -t 'text_to_encrypt' -s -l 'YoutubeLink' --start_time='HH:MM:SS' --end_time='HH:MM:SS'")
    print("To encrypt file: AESTube.py -e -f '<file_to_encrypt>' -s -l 'YoutubeLink' --start_time='HH:MM:SS' --end_time='HH:MM:SS'")
    print("To encrypt text: AESTube.py -d -t 'text_to_decrypt' -s -l 'YoutubeLink' --start_time='HH:MM:SS' --end_time='HH:MM:SS'")
    print("To decrypt file: AESTube.py -d -f '<file_to_decrypt>' -s -l 'YoutubeLink' --start_time='HH:MM:SS' --end_time='HH:MM:SS'")
    print("--------------------Local Files--------------------")
    print("To encrypt file: AESTube.py -e -f '<file_to_encrypt>' -s -w '<file name.extension>' --start_time='HH:MM:SS' --end_time='HH:MM:SS'")
    print("To decrypt file: AESTube.py -d -f '<file_to_decrypt>' -s -w '<file name.extension>' --start_time='HH:MM:SS' --end_time='HH:MM:SS'")
    print("--------------------Examples--------------------")
    print("AESTube_adjv3_1.py -e -f 'image1.png' -v -l 'https://www.youtube.com/watch?v=nd6pq74vAlA'")
    print("AESTube_adjv3_1.py -d -f 'image1.png.aenc' -v -l 'https://www.youtube.com/watch?v=nd6pq74vAlA'")
    print("AESTube_adjv3_1.py -e -t 'Hello World' -s -w '1.wav' --start_time='00:00:30' --end_time='00:01:00'")
    print("AESTube_adjv3_1.py -d -t 'tO702AktmkSVoiuHM59U8kMcG8hE16pvgIBDLmRqCac=' -s -w '1.wav' --start_time='00:00:30' --end_time='00:01:00'")
    print("--------------------User Error--------------------")
    print("In theory if you don't have a wav file, you can just enter the three letter ext and it will convert to wav. It looks like this:")
    print("AESTube_adjv3_1.py -e -f 'image1.png' -v -w 'key.mp3'")

#Function to find the closer element in an array
def closest(lst, K): 
    return lst[min(range(len(lst)), key = lambda i: abs(lst[i]-K))] 

#Function to match Hz with note name
def matchingFreq(freq):
    freq_array = [16.351, 17.324, 18.354, 19.445, 20.601, 21.827, 23.124, 24.499, 25.956, 27.500, 29.135, 30.868] # 0 scale float values
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'] #TODO maybe add all semitones to improve complexity
    scale_multiplier = 0    #Could be used to restrict notes by multiples
    current_note=0
    for i in range(len(freq_array)*scales):
        if(i%len(freq_array) == 0):
            freq_array=[element * 2 for element in freq_array]
            scale_multiplier += 1
        current_note = freq_array[i%len(notes)]
        if(freq < current_note):  
            return notes[freq_array.index(closest(freq_array, freq))] + str(scale_multiplier-1)
    return 'Unknown'

#Function that filter silences, not audible and repeated data in found freqs.
def filterFrequencyArray(unfiltered_freqs):                                      
    filtered_freqs=[]
    for i in range (len(unfiltered_freqs)-1):
            if(unfiltered_freqs[i]>15.0 and unfiltered_freqs[i]<8000):
                if(matchingFreq(unfiltered_freqs[i])!=matchingFreq(unfiltered_freqs[i+1])):
                    filtered_freqs.append(unfiltered_freqs[i])
    return filtered_freqs

#Removes consecutive duplication in final notes array.
def removeRepeatedNotes(detected_notes):
    filtered_notes=[]
    for i in range(len(detected_notes)-1):
        if(detected_notes[i]!=detected_notes[i+1]):
            filtered_notes.append(detected_notes[i])
    filtered_notes.append(detected_notes[i+1])        
    return filtered_notes        
    
#Almost all the magic is done in this function. It reads, splits, operates and detect frequencies.
def noteDetect(audio_file):
    file_length = audio_file.getnframes()
    window_size = int(file_length*0.01)
    if(isVerbose): 
        print(f'Audio Length: {str(window_size)} bytes')
    
    #Clearing arrays to allow reuse of function
    detected_freqs.clear()

    for i in range(int(file_length/window_size)):
        data = audio_file.readframes(window_size)
        data = struct.unpack('{n}h'.format(n=window_size), data)
        sound = np.array(data) 
        #sound = np.divide(sound, float(2**15))
        #window = sound * np.blackman(len(sound))
        f = np.fft.fft(sound)
        i_max = np.argmax(abs(f))
        #DEBUG print("Fourier (abs) value: " + str(i_max))
        freq = round((i_max * fs)/len(sound),3) #Freqs rounded to 3 decimals
        detected_freqs.append(freq)
    audio_file.close() #Close audio file
    clean_freqs = filterFrequencyArray(detected_freqs)
    if(isVerbose):
        print('-----RAW Frequencies array-----')
        print(*detected_freqs)
        print('-----Cleaned Frequencies array-----')
        print(*clean_freqs)
    for freq in clean_freqs:
            detected_notes.append(matchingFreq(freq))
    return removeRepeatedNotes(detected_notes)

def soundProcessing(file_name):
    try:
        sound_file = wave.open( f'{file_name}.wav', 'r')
        print('Conversion completed. Now starting to analize.')
        print('----------------------------------------------')
        filtered_notes= noteDetect(sound_file) #To audio processing with FFT
        if(isVerbose):
            print("Approximated Notes: " + str(filtered_notes))
    except IOError:
        print('[Error] reading file')

def splitAudio(startTime, endTime, file_name):
    command=f"ffmpeg -i '{file_name}.wav' -ss '{startTime}' -to '{endTime}' -c copy '{file_name}_split.wav'"
    try:
        subprocess.check_call(['ffmpeg', '-version'])
    except subprocess.CalledProcessError:
        print('FFMpeg not installed. It is used during conversion process.')
        sys.exit()
    if(isVerbose):
        subprocess.call(command, shell=True)
    else:
        FNULL = open(os.devnull, 'wb')
        subprocess.call(command, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)

#Binary file to b64 then to utf-8 string
def readBinFile(filepath):
    try:
        raw_data = open(filepath, "rb").read()
        return raw_data
    except IOError:
        print('[Error] Reading file')
        sys.exit()

#Base 64 data to binary file
def writeBinToFile(data,filename):
    try:
        newFile = open(filename, 'wb')
        newFile.write(data) #Write binary
        newFile.close()
    except IOError:
        print('[Error] Writing to file')

def download_audio(url):
    ydl_opts = {
        'verbose': True,
        'format': 'best',
        'noplaylist': True,
        'outtmpl': 'key.%(ext)s',
        'restrictfilenames':True,
        'forcefilename': True,
        }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.cache.remove()
        vid_info = ydl.extract_info(url, None)
        filename = ydl.prepare_filename(vid_info)
        ydl.download([url])

    ext=filename.split('.')[1]
    command= f"ffmpeg -y -i 'key.{ext}' -ab 96k -ac 1 -ar 44100 -vn 'key.wav'"
    if(isVerbose):
        print(command)
    #print(f'Converting to wav: {vid_title}')
    print('Converting to wav:  %s' % vid_info['title'])
    try:
        subprocess.check_call(['ffmpeg', '-version'])
    except subprocess.CalledProcessError:
        print('FFMpeg not installed. It is used during conversion process.')
        sys.exit()
    if(isVerbose):
        subprocess.call(command, shell=True)
    else:
        FNULL = open(os.devnull, 'wb')
        subprocess.call(command, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)

def fixExtension(file_name, ext):
    command= f"ffmpeg -y -i '{file_name}.{ext}' -ab 96k -ac 1 -ar 44100 -vn -c copy '{file_name}.wav'"
    try:
        subprocess.check_call(['ffmpeg', '-version'])
    except subprocess.CalledProcessError:
        print('FFMpeg not installed. It is used during conversion process.')
        sys.exit()
    if(isVerbose):
        subprocess.call(command, shell=True)
    else:
        FNULL = open(os.devnull, 'wb')
        subprocess.call(command, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)

if __name__ == "__main__":
    getArgsOptions()
    if(opSource == 'L'):
        download_audio(ytLink)
        file_name = 'key.wav'
    if(opSource == 'W'):
        file_name = localfile

    if(isVerbose):
        print(file_name)
    ext=file_name.split('.')[1]
    #Just deletes .mp4
    filename_no_ext=file_name.split('.')[0]
    if(isVerbose):
        print(filename_no_ext)

    if(isVerbose):
        print(ext)
    if(isSplitted):
        splitAudio(startTime, endTime, filename_no_ext)
        if(ext == 'wav'):
            soundProcessing(filename_no_ext)
        else:
            fixExtension(filename_no_ext, ext)
            soundProcessing(filename_no_ext)
    else:
        if(ext == 'wav'):
            soundProcessing(filename_no_ext)
        else:
            fixExtension(filename_no_ext, ext)
            soundProcessing(filename_no_ext)

    #Creating key for encryption
    key=''
    for note in detected_notes:
        key += note
    aes=AESCipher(key)
    if(opMode=='E'): #Encryption
        if(opType =='T'): #Text mode
            print(f'Encrypted text: {aes.encrypt(opData.encode(),encode=True)}')
        else:   #File mode
            encryptedData = aes.encrypt(readBinFile(opData), encode=False)
            writeBinToFile(encryptedData, f'{opData}.aenc')
    else:
        if(opType=='T'): #Text mode
            print(f'Decrypted text: {aes.decrypt(opData,decode=True).decode()}')
        else:   #File mode
            decryptedData = aes.decrypt(readBinFile(opData), decode=False)
            writeBinToFile(decryptedData, opData[0:len(opData)-5]) #Binary write deleting aenc extension
            
