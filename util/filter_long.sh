#!/bin/env bash

mkdir long 2>/dev/null
ls | while read i; do 
	echo -- $i
 	secs=$(ffprobe -i "$i" -show_entries format=duration -v quiet -of csv="p=0" | sed 's/\..*//'); 
 	if (( $secs > 1200 )); then 
 		echo -- moving $i; 
 		mv -- "$i" long/.; 
 	fi; 
done
