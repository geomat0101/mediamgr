#!/bin/env bash

# this is a media compositor to make vlc happy

# we are creating a directory called 'combined' that contains links to
# all the files in the mp4/ and img/ directories

# For vlc to be able to work with both images and videos in the same directory
# we are giving the img links an additional '.mp4' extension.  This causes
# vlc's image demuxer to automatically turn the image into a short video.
# (see vlc CODEC prefs to set video length)

if [[ ! -d combined ]]; then
	echo no existing combined dir found
	exit 1;
fi

rm -rf combined
mkdir combined
ls mp4 | while read i; do ln mp4/$i combined/$i; done
ls img | while read i; do ln img/$i combined/$i.mp4; done

