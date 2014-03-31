"""Module that starts the JVM when imported. 

This is the easy way to make it possible to start the JVM on demand
but avoid trying to start it twice.

"""

import os
import javabridge
import bioformats

def start_cpa_jvm():
    javabridge.start_vm(class_path=bioformats.JARS,
                        run_headless=True)
    javabridge.attach()

start_cpa_jvm()

    
