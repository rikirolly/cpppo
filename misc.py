
# 
# Cpppo -- Communication Protocol Python Parser and Originator
# 
# Copyright (c) 2013, Hard Consulting Corporation.
# 
# Cpppo is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.  See the LICENSE file at the top of the source tree.
# 
# Cpppo is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# 


from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

__author__                      = "Perry Kundert"
__email__                       = "perry@hardconsulting.com"
__copyright__                   = "Copyright (c) 2013 Hard Consulting Corporation"
__license__                     = "GNU General Public License, Version 3 (or later)"
__version__			= "0.01"

"""
Miscellaneous functionality used by various other modules.
"""

import logging
import math
import sys
import timeit
try:
    import reprlib
except ImportError:
    import repr as reprlib

# 
# misc.timer
# 
# Select platform appropriate timer function
timer				= timeit.default_timer

# 
# misc.nan	-- IEEE NaN (Not a Number)
# misc.isnan	-- True iff the provided value is nan
# misc.inf	-- IEEE inf (Infinity)
# misc.isinf	-- True iff the provided value is inf
# 
#     Augment math with some useful constants.  Note that IEEE NaN is the
# only floating point number that won't equal itself.
# 
#     Numpy has these, but we can't assume it is available.
# 
if hasattr( math, 'nan' ):
    nan                         = math.nan
else:
    nan                         = float( 'nan' )
    math.nan                    = nan
if hasattr( math, 'isnan' ):
    isnan                       = math.isnan
else:
    def isnan( f ):
        return f != f
    math.isnan = isnan

if hasattr( math, 'inf' ):
    inf				= math.inf
else:
    inf				= float( 'inf' )
    math.inf			= inf
if hasattr( math, 'isinf' ):
    isinf			= math.isinf
else:
    def isinf( f ):
        return abs( f ) == inf
    math.isinf = isinf

# 
# logging.normal	-- regular program output 
# logging.detail	-- detail in addition to normal output
# 
#     Augment logging with some new levels, between INFO and WARNING, used for normal/detail output.
# 
#      .WARNING 	       == 30
logging.NORMAL			= logging.INFO+5
logging.DETAIL			= logging.INFO+3
#      .INFO    	       == 20

logging.addLevelName( logging.NORMAL, 'NORMAL' )
logging.addLevelName( logging.DETAIL, 'DETAIL' )

def __normal( self, msg, *args, **kwargs ):
    if self.isEnabledFor( logging.NORMAL ):
        self._log( logging.NORMAL, msg, args, **kwargs )

def __detail( self, msg, *args, **kwargs ):
    if self.isEnabledFor( logging.DETAIL ):
        self._log( logging.DETAIL, msg, args, **kwargs )

logging.Logger.normal		= __normal
logging.Logger.detail		= __detail

# 
# function_name -- Attempt to elaborate on the module/class heritage of the given function
#
def function_name( f ):
    if hasattr( f, '__module__' ):
        return f.__module__ + '.' + f.__name__
    elif hasattr( f, 'im_class' ):
        return f.im_class.__module__ + '.' + f.im_class.__name__ + '.' + f.__name__
    return f.__name__
    
# 
# near          -- True iff the specified values are within 'significance' of each-other
# 
def near( a, b, significance = 1.0e-4 ):
    """ Returns True iff the difference between the values is within the factor 'significance' of
    one of the original values.  Default is to within 4 decimal places. """
    return abs( a - b ) <= significance * max( abs( a ), abs( b ))

# 
# clamp         -- Clamps a value to within a tuple of limits.
# 
#     Limits that are math.nan are automatically ignored, with no special code (comparisons
# against NaN always return False).
# 
#     The ordering of 'lim' is assumed to be (min, max).  We don't attempt to reorder, because 'lim'
# may contain NaN.
# 
def clamp( val, lim ):
    """ Limit val to between 2 (optional, if nan) limits """
    if ( val < lim[0] ):
        return lim[0]
    if ( val > lim[1] ):
        return lim[1]
    return val

# 
# scale         -- Transform a value from one range to another, without clipping
#
#     No math.nan allowed or zero-sized domains or ranges.  Works for either increasing or
# decreasing ordering of domains or ranges.  If clamped, we will ensure that the rng is (re)ordered
# appropriately.
# 
def scale( val, dom, rng, clamped=False ):
    """Map 'val' from domain 'dom', to new range 'rng'"""
    result                      = ( rng[0]
                                    + ( val    - dom[0] )
                                    * ( rng[1] - rng[0] )
                                    / ( dom[1] - dom[0] ))
    if clamped:
        result                  = clamp( result, (min(rng), max(rng)))
    return result

# 
# magnitude     -- Return the approximate base magnitude of the value, in 'base' ( 10 )
#
#     Handy for computing up/down modifiers for values.  For example:
#
#      23 ==> 1.
#     .23 ==>  .1
# 
# The magnitude shifts to the next higher value about 1/4 of the way
# past each multiple of base.

def magnitude( val, base = 10 ):
    if val <= 0:
        return nan
    return pow( base, round( math.log( val, base )) - 1 )


# 
# reprargs(args,kwds)	-- log args/kwds in sensible fashion
# @logresult(prefix,log)-- decorator to log results/exception of function
# lazystr		-- lazily evaluate expensive string formatting
# 
def reprargs( *args, **kwds ):
    return ", ".join(   [ reprlib.repr( x ) for x in args ]
                      + [ "%s=%s" % ( k, reprlib.repr( v ))
                          for k,v in kwds.items() ])


def logresult( prefix=None, log=logging ):
    import functools
    def decorator( function ):
        @functools.wraps( function )
        def wrapper( *args, **kwds ):
            try:
                result		= function( *args, **kwds )
                log.debug( "%s-->%r" % (
                        prefix or function.__name__+'('+reprargs( *args, **kwds )+')', result ))
                return result
            except Exception as e:
                log.debug( "%s-->%r" % (
                        prefix or function.__name__+'('+reprargs( *args, **kwds )+')', e ))
                raise
        return wrapper
    return decorator


class lazystr( object ):
    """Evaluates the given function returning a str lazily, eg:
           logging.debug( lazystr( lambda: \
               "Some expensive operation: %d" % ( obj.expensive() )))
       vs.:
           logging.debug(
               "Some expensive operation: %d", obj.expensive() )
    """
    __slots__ = '_function'
    def __init__( self, function ):
        self._function		= function
    def __str__( self ):
        return self._function()


# 
# sort order key=... methods
# 
# natural	-- Strings containing numbers sort in natural order
# nan_first	-- NaN/None sorts lower than any number
# nan_last	-- NaN/None sorts higher than any number
# 
# 
def natural( string, fmt="%9s", ):
    '''A natural sort key helper function for sort() and sorted() without using
    regular expressions or exceptions. 

    In python2, incomparable types (eg. str and bool) were compared based on
    (arbitrary) conventions (eg. type name, object ID).  In Python3,
    incomparable types raise exceptions.  So, all types must be converted to a
    common comparable type; str, and non-numeric types are 

    >>> items = ('Z', 'a', '10th', '1st', '9')
    >>> sorted(items)
    ['10th', '1st', '9', 'Z', 'a']
    >>> sorted(items, key=natural)
    ['1st', '9', '10th', 'a', 'Z']    
    '''
    if type( string ) in natural.num_types:
        # Convert numerics to string; sorts 9.3 and '9.3' as equivalent
        string = str(string)
    if not isinstance( string, natural.str_type ):
        # Convert remaining types compare as ('',<type name>,<hash>/<id>), to
        # sorts objects of same type in an orderly fashion.   If __has__ exists
        # but is None, indicates not hash-able.
        res = ('', string.__class__.__name__, 
               hash( string ) if hasattr( string, '__hash__' ) and string.__hash__ is not None
               else id( string ))
    else:
        res = []
        for c in string:
            if c.isdigit():
                if res and type( res[-1] ) in natural.num_types:
                    res[-1] = res[-1] * 10 + int( c )
                else:
                    res.append( int( c ))
            else:
                res.append( c.lower() )
    return tuple( (( fmt % itm ) if type( itm ) in natural.num_types
                   else itm )
                  for itm in res )

natural.str_type 	= ( basestring if sys.version_info.major < 3
                            else str )
natural.num_types	= ( (float, int, long) if sys.version_info.major < 3
                            else (float, int))


def non_value( number ):
    return number is None or isnan( number )

def nan_first( number ):
    if non_value( number ):
        return -inf
    return number

def nan_last( number ):
    if non_value( number ):
        return inf
    return number

# 
# centeraxis	-- center string in width around a (rightmost) axis character
# 
def centeraxis( string, width, axis='.', fillchar=' ', reverse=False, clip=False,
                left_right=lambda w: (w // 2, w - w // 2) ):
    string		= str( string )
    pos			= string.find( axis ) if reverse else string.rfind( axis )
    if pos < 0:
        # No axis cahr
        if reverse:
            pos, string	= len( string ), string
        else:
            # ... but it would normally be on the right
            pos, string	= 0,             fillchar + string
    left, rght		= string[0:pos], string[pos:] # axis char will be on rght
    lwid, rwid		= left_right( width )
    #print("left: %s (%d), rght: %s (%d)" % ( left, lwid, rght, rwid ))
    if len( left ) < lwid:
        left		= fillchar * ( lwid - len( left )) + left
    elif clip:
        left		= left[-lwid:]
    if len( rght ) < rwid:
        rght	       += fillchar * ( rwid - len( rght ))
    elif clip:
        rght		= rght[:rwid]
    return left+rght