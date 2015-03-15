Simple Python script that allows smugmug.com users to rename their keywords in bulk.  Uses Python and the smugmug REST API.

NOTE that I haven't used this in over 4 years, and it may very well have rotted.  I just (November 6, 2011) received an email from someone who tried to use it, reporting a bug with a stacktrace ending in:

> AttributeError: No child element named 'Albums'

But all is not lost!  The person reporting the bug also found a workaround on the smugmug site itself:

"""
A little more searching, and I discovered that it's possible to do through smugmug, by first going to the (automatic) gallery for that keyword, then using the "Captions/Keywords" tool for that gallery.
"""