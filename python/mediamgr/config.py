arango_url="http://mediamgr.is-leet.com:8529"
arango_dbname="mediamgr"
arango_username="mediamgr"
arango_password="mediamgr"

# this is to keep from blowing out GPU memory
# downsize large images so the max edge length is the target,
# then upsample the configured number of times when detecting faces
#
# downsize_target=1024, upscale_times=2 results in a process that
# uses about 4GB on a RTX 3080
downsize_target=1024
upsample_times=2

# use 'cnn' if you have a GPU and dlib is built with cuda support
# use 'hog' if you want to use the regular CPU (slower)
#detection_model="hog"
detection_model="cnn"

# how many points to describe a face, 5 or 68?
# large is more accurate, slower
#shape_predictor_model="small"
shape_predictor_model="large"

# How many times to re-sample the face when calculating encoding. 
# Higher is more accurate, but slower (i.e. 100 is 100x slower)
# The default of 1 is already > 99% accurate, but 100 can get
# close to 99.4% if desired
encoding_jitters=1