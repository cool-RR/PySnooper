# PySnooper - Never use print for debugging again #

**PySnooper** is a poor man's debugger.

You're trying to figure out why your Python code isn't doing what you think it should be doing. You'd love to use a full-fledged debugger with breakpoints and watches, but you can't be bothered to set one up right now.

You're looking at a section of Python code. You want to know which lines are running and which aren't, and what the values of the local variables are. 

Most people would use a `print` line. Probably several of them, in strategic locations, some of them showing the values of variables. Then they'd use the output of the prints to figure out which code ran when and what was in the variables.

**PySnooper** lets you do the same, except instead of carefully crafting the right `print` lines, you just add one decorator line to the function you're interested in. You'll get a play-by-play log of your function, including which lines ran and   when, and exactly when local variables were changed.

What makes **PySnooper** stand out from all other code intelligence tools? You can use it in your shitty, sprawling enterprise codebase without having to do any setup. Just slap the decorator on, as shown below, and redirect the output to a dedicated log file by specifying its path as the first argument.

# Example #

We're writing a function that converts a number to binary, by returing a list of bits. Let's snoop on it by adding the `@pysnooper.snoop()` decorator:

    import pysnooper
    
    @pysnooper.snoop()
    def number_to_bits(number):
        if number:
            bits = []
            while number:
                number, remainder = divmod(number, 2)
                bits.insert(0, remainder)
            return bits
        else:
            return [0]
        
    number_to_bits(6)

The output to stderr is: 
    
                ==> number = 6
    00:24:15.284000 call         3 @pysnooper.snoop()
    00:24:15.284000 line         5     if number:
    00:24:15.284000 line         6         bits = []
                ==> bits = []
    00:24:15.284000 line         7         while number:
    00:24:15.284000 line         8             number, remainder = divmod(number, 2)
                ==> number = 3
                ==> remainder = 0
    00:24:15.284000 line         9             bits.insert(0, remainder)
                ==> bits = [0]
    00:24:15.284000 line         7         while number:
    00:24:15.284000 line         8             number, remainder = divmod(number, 2)
                ==> number = 1
                ==> remainder = 1
    00:24:15.284000 line         9             bits.insert(0, remainder)
                ==> bits = [1, 0]
    00:24:15.284000 line         7         while number:
    00:24:15.284000 line         8             number, remainder = divmod(number, 2)
                ==> number = 0
    00:24:15.284000 line         9             bits.insert(0, remainder)
                ==> bits = [1, 1, 0]
    00:24:15.284000 line         7         while number:
    00:24:15.284000 line        10         return bits
    00:24:15.284000 return      10         return bits


# Features #

If stderr is not easily accessible for you, you can redirect the output to a file easily:

    @pysnooper.snoop('/my/log/file.log')
    
Want to see values of some variables that aren't local variables?

    @pysnooper.snoop(variables=('foo.bar', 'self.whatever'))
    
    
# Installation # 

Use `pip`:

    pip install pysnooper


# Copyright #

Copyright (c) 2019 Ram Rachum, released under the MIT license.