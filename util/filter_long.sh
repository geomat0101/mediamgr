#!/bin/env bash

# use ffprobe from ffmpeg package to get length of video and moves it into a 'long' subdir
# if it's longer than 1200 seconds (20 mins)

mkdir long 2>/dev/null
ls | while read i; do 
	echo -- $i
 	secs=$(ffprobe -i "$i" -show_entries format=duration -v quiet -of csv="p=0" | sed 's/\..*//'); 
 	if (( $secs > 1200 )); then 
 		echo -- moving $i; 
 		mv -- "$i" long/.; 
 	fi; 
done
