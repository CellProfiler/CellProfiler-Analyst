"""Module that starts the JVM when imported. 

This is the easy way to make it possible to start the JVM on demand
but avoid trying to start it twice.

"""

import os
import javabridge
import bioformats

def start_cpa_jvm():
    class_path = os.pathsep.join(bioformats.JARS)
    javabridge.start_vm(['-Djava.class.path=' + class_path],
                        run_headless=True)
    javabridge.attach()

start_cpa_jvm()

    
