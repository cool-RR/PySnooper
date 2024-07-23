# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

from wrapper import snoop_wrapper
import sys

def main():
    #TODO: Add flags for different options
    if sys.argv[1] == "-m": #python3 -m pysnooper <file path> <file arguments> 
        snoop_wrapper()
    if sys.argv[1] =='h':
        print("Usage: python3 -m pysnooper <file path> <file arguments>")
        sys.exit(1)

if __name__ == '__main__': 
    #TODO: Add flags for different options
    #TODO: Assertions 
    
  main()
