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
from shutil import copyfile


fs= 44100               #Sample Hz
scales = 12             #Amount of musical scales to work with (12 semitones)
duration = 0            #Audio duration in ms to control splitting
detected_notes = []     #Array to store detected notes
detected_freqs = []     #Array to store detected frequencies
ytLink = file_name = localfile = opData = opMode = opType = opSource = key = ''
isSplitted = isInvalid = isVerbose = False
startTime = endTime = ''
path = 'mediafiles/'

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
    #freq_array = [16.351, 17.324, 18.354, 19.445, 20.601, 21.827, 23.124, 24.499, 25.956, 27.500, 29.135, 30.868] # 0 scale float values
    #notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'] #TODO maybe add all semitones to improve complexity
    freq_array = [16.35, 17.32, 18.35, 19.45, 20.60, 21.83, 23.12, 24.50, 25.96, 27.50, 29.14, 30.87, 32.70, 34.65, 36.71, 38.89, 41.20, 43.65, 46.25, 49.00, 51.91, 55.00, 58.27, 61.74, 65.41, 69.30, 73.42, 77.78, 82.41, 87.31, 92.50, 98.00, 103.83, 110.00, 116.54, 123.47, 130.81, 138.59, 146.83, 155.56, 164.81, 174.61, 185.00, 196.00, 207.65, 220.00, 233.08, 246.94, 261.63, 277.18, 293.66, 311.13, 329.63, 349.23, 369.99, 392.00, 415.30, 440.00, 466.16, 493.88, 523.25, 554.37, 587.33, 622.25, 659.26, 698.46, 739.99, 783.99, 830.61, 880.00, 932.33, 987.77, 1046.50, 1108.73, 1174.66, 1244.51, 1318.51, 1396.91, 1479.98, 1567.98, 1661.22, 1760.00, 1864.66, 1975.53, 2093.00, 2217.46, 2349.32, 2489.02, 2637.02, 2793.83, 2959.96, 3135.96, 3322.44, 3520.00, 3729.31, 3951.07, 4186.01, 4434.92, 4698.64, 4978.03, 5274.04, 5587.65, 5919.91, 6271.93, 6644.88, 7040.00, 7458.62, 7902.13]
    notes = ['C0', 'C#0', 'D0', 'D#0', 'E0', 'F0', 'F#0', 'G0', 'G#0', 'A0', 'A#0', 'B0', 'C1', 'C#1', 'D1', 'D#1', 'E1', 'F1', 'F#1', 'G1', 'G#1', 'A1', 'A#1', 'B1', 'C2', 'C#2', 'D2', 'D#2', 'E2', 'F2', 'F#2', 'G2', 'G#2', 'A2', 'A#2', 'B2', 'C3', 'C#3', 'D3', 'D#3', 'E3', 'F3', 'F#3', 'G3', 'G#3', 'A3', 'A#3', 'B3', 'C4', 'C#4', 'D4', 'D#4', 'E4', 'F4', 'F#4', 'G4', 'G#4', 'A4', 'A#4', 'B4', 'C5', 'C#5', 'D5', 'D#5', 'E5', 'F5', 'F#5', 'G5', 'G#5', 'A5', 'A#5', 'B5', 'C6', 'C#6', 'D6', 'D#6', 'E6', 'F6', 'F#6', 'G6', 'G#6', 'A6', 'A#6', 'B6', 'C7', 'C#7', 'D7', 'D#7', 'E7', 'F7', 'F#7', 'G7', 'G#7', 'A7', 'A#7', 'B7', 'C8', 'C#8', 'D8', 'D#8', 'E8', 'F8', 'F#8', 'G8', 'G#8', 'A8', 'A#8', 'B8']
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
        #freq = round((i_max * fs)/len(sound),3) #Freqs rounded to 3 decimals
        freq = round((i_max * fs)/len(sound),2) #Freqs rounded to 2 decimals for use with larger set
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
        sound_file = wave.open( f'mediafiles/{file_name}.wav', 'r')
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
        'outtmpl': 'mediafiles/key.%(ext)s',
        'restrictfilenames':True,
        'forcefilename': True,
        }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.cache.remove()
        vid_info = ydl.extract_info(url, None)
        filename = ydl.prepare_filename(vid_info)
        ydl.download([url])

    ext=filename.split('.')[1]
    name = filename.split('.')[0]
    name = name.split('/')[1]
    #command= f"ffmpeg -y -i 'key.{ext}' -ab 96k -ac 1 -ar 44100 -vn 'key.wav'"
    if(opMode=='E'):
        command = "./convert.sh"
    else:
        command = "./deconvert.sh"

    f = open("varfile.txt", "w")
    f.write(ext)
    f.close()

    f = open("name.txt", "w")
    f.write(name)
    f.close()

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

def localMixUp(filename):
    ext=filename.split('.')[1]
    name = filename.split('.')[0]
    dst = f'mediafiles/{filename}'
    src = filename
    path = 'mediafiles/'

    if(opMode=='E'):
        command = "./convert.sh"
    else:
        command = "./deconvert.sh"

    f = open("varfile.txt", "w")
    f.write(ext)
    f.close()

    f = open("name.txt", "w")
    f.write(name)
    f.close()

    os.mkdir(path)
    copyfile(src, dst)

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
        localMixUp(file_name)

    if(isVerbose):
        print(file_name)
    ext=file_name.split('.')[1]
    #filename_no_ext = file_name[0:len(file_name)-4] #Just deletes .mp4
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

    files = glob.glob(f'mediafiles/*')
    for f in files:
        os.remove(f)    #Deleting remaining media files
    os.rmdir(path)


    
    
