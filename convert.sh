#!/bin/bash
file_ext=`cat varfile.txt`
rm varfile.txt
name=`cat name.txt`
rm name.txt
#mkdir mediafiles
#cp key.$file_ext mediafiles/
cd mediafiles/
ffmpeg -y -i $name.$file_ext -ab 96k -ac 2 -ar 44100 -vn start.wav
ffmpeg -i start.wav -filter_complex \
"[0:0]pan=1|c0=c0[left]; \
 [0:0]pan=1|c0=c1[right]" \
-map "[left]" left.wav -map "[right]" right.wav
ffmpeg -i right.wav -af areverse rright.wav
ffmpeg -i left.wav -i rright.wav -filter_complex join=inputs=2:channel_layout=stereo output.wav
mkdir splits
ffmpeg -i output.wav -f segment -segment_time 7 -c copy splits/out%03d.wav
for f in splits/*.wav; do echo "file '$f'" >> mylist.txt; done
shuf mylist.txt > adjlist.txt
ffmpeg -f concat -safe 0 -i adjlist.txt -c copy mixed.wav
#sort adjlist.txt > mylist.txt to undo might be needed idk
#you could use the start of this for a public key encryption but that's beyond me atm
ffmpeg -y -i mixed.wav -ab 96k -ac 1 -ar 44100 -vn key.wav
mv adjlist.txt ..
rm -rf splits/
cd ..
