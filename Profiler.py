import subprocess, os
import pstats
import StringIO
import cProfile

# TODO: 
# make methods for extracting the data for use in reports.
# High level data such as overall time and detailed function data.

class Profiler:
    
  def __init__(self, config):
    stream = StringIO.StringIO()
    stats = pstats.Stats('restats', stream=stream)
    stats.sort_stats('cumulative').dump_stats('restats')
    stats.print_stats()
    profileFile = open(config['profileFilename'], "w")
    profileFile.write(stream.getvalue())
    profileFile.close()    
    return
  
  