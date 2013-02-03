import os
import boto
import simplejson
import twitter
import random
import cv
import sys
import time
import Image
import subprocess
import util
import errors

tesseract_exe_name = 'tesseract' # Name of executable to be called at command line
scratch_image_name = "temp.bmp" # This file must be .bmp or other Tesseract-compatible format
scratch_text_name_root = "temp" # Leave out the .txt extension
cleanup_scratch_flag = True  # Temporary files cleaned up after OCR operation
cfg_fname = os.environ['HOME']+'/.twit.cfg'
fp = open(cfg_fname, 'r')
c_k = fp.readline().strip()
c_s = fp.readline().strip()
a_k = fp.readline().strip()
a_s = fp.readline().strip()
fp.close()

def process_frame(filename, bucket, key):
    #Open the file
    print '  > processing \'' + filename + '\''
    #fp = open(filename, "r")
    #lines = fp.readlines()
    #lines = ['testing a long tweet',' this should get',
    #'interesting and should generate an',' html file to',
    #'display the result.  hmmmmm mmmmmmmmmmmmmmmmmmmmm ',
    #'mmmmmmmmmmmmmmmmmm mmmmmmmmmmmmmm mmmmmmmmmmmm ',
    #'mmmmmmmmm mmmmmmmmm', ' what a strange tweet...']
    #text = str(random.randint(0, 1000))
    #for l in lines:
        #text = text + l

    #Do OCR on the file
    text = image_file_to_string(filename, graceful_errors=True);
    text = text.strip()

    #Ignore the frame if no text found
    if len(text) == 0:
        print '  > frame contained no discernable text'
        return

    #Tweet the contents if possible
    #otherwise generate a html file and tweet that
    print '  > found text.'
    print '  > generating tweet.'
    url = 'https://s3.amazonaws.com/mhacks_iris/'+key.name
    text = text.strip() + ' ' + url
    if len(text) < 140:
        #tweet the line
        print '  > tweeting:'
        print '  > \'' + text + '\''
    else:
        print '  > tweet too large.'

        print '  > generating html file.'
        html = '<html><body>'
        html = html + '<p>' + text.strip(url) + '</p>'
        html = html + '<img src=\"'+url+'\" alt=\"capture\">'
        html = html + '</body></html>'

        print '  > uploading html to s3'
        key_uqname = key.name.split('/')[1]
        html_key = bucket.new_key('html/'+key_uqname+'.html')
        html_key.set_contents_from_string(html)
        html_key.set_acl('public-read')
        
        print '  > generating new url'
        text = 'Look what I just saw at #mhacks https://s3.amazonaws.com/mhacks_iris/'+html_key.name
        print '  > ' + text

    #Send the tweet!
    print '  > tweeting...'
    acn = connect_twitter()
    try:
        status=acn.PostUpdates(text)
    except:
        print '  > failure :-('
        return
    print '  > success!'
    return

def connect_twitter():
    acn = twitter.Api(
            consumer_key=c_k,
            consumer_secret=c_s,
            access_token_key=a_k,
            access_token_secret=a_s)
    
    return acn

def call_tesseract(input_filename, output_filename):
    """Calls external tesseract.exe on input file (restrictions on types),
    outputting output_filename+'txt'"""
    args = [tesseract_exe_name, input_filename, output_filename]
    proc = subprocess.Popen(args)
    retcode = proc.wait()
    if retcode!=0:
        errors.check_for_errors()

def image_to_string(im, cleanup = cleanup_scratch_flag):
    """Converts im to file, applies tesseract, and fetches resulting text.
    If cleanup=True, delete scratch files after operation."""
    try:
        util.image_to_scratch(im, scratch_image_name)
        call_tesseract(scratch_image_name, scratch_text_name_root)
        text = util.retrieve_text(scratch_text_name_root)
    finally:
        if cleanup:
            util.perform_cleanup(scratch_image_name, scratch_text_name_root)
    return text

def image_file_to_string(filename, cleanup = cleanup_scratch_flag, graceful_errors=True):
    """Applies tesseract to filename; or, if image is incompatible and graceful_errors=True,
    converts to compatible format and then applies tesseract.  Fetches resulting text.
    If cleanup=True, delete scratch files after operation."""
    try:
        try:
            call_tesseract(filename, scratch_text_name_root)
            text = util.retrieve_text(scratch_text_name_root)
        except errors.Tesser_General_Exception:
            if graceful_errors:
                im = Image.open(filename)
                text = image_to_string(im, cleanup)
            else:
                raise
    finally:
        if cleanup:
            util.perform_cleanup(scratch_image_name, scratch_text_name_root)
    return text
