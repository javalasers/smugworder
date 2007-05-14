#!/usr/bin/env python
#
# smugworder - Bulk keyword renaming for smugmug.com.
# Copyright 2007  Will Robinson
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""smugworder - Bulk keyword renaming for smugmug.com.

For usage information, run:
  smugworder.py --help
"""

__author__ = 'willrobinson@gmail.com (Will Robinson)'
__copyright__ = "Copyright 2007 Will Robinson. GNU GPL 2."

import xmltramp
import urllib
import sys
import csv
import optparse

_BASE = 'https://api.smugmug.com/hack/rest/1.1.1/?'


def _SendMessage(method_name, **kwds):
  """Sends a request to the Smugmug server.

  Args:
    method_name: Name of the smugmug method we're invoking.
      Shouldn't include the 'smugmug.' prefix.
    kwds: We'll use these as arguments in the request we send.

  Returns: A file-like object containing the content of the response.
  """
  kwds['method'] = 'smugmug.' + method_name
  args = urllib.urlencode(kwds)
  return urllib.urlopen(_BASE + args)


def Login(email, password):
  """Logs in with the given email and password.  Returns a session id.
  """
  r = xmltramp.seed(
    _SendMessage('login.withPassword',
                 EmailAddress=email,
                 Password=password,
                 APIKey='3CNbe5jSvJ682lASTajS6LeHa6muVUV7'))
  return str(r.Login.SessionID)


def GetAlbumIds(sessionid):
  """Gets a list of all album ids for the user.
  """
  r = xmltramp.seed(_SendMessage('albums.get', SessionID=sessionid))
  return [long(album('id')) for album in r.Albums[:]]


def GetImageIds(sessionid, albumid):
  """Returns a list of image ids for the given album.
  """
  r = xmltramp.seed(
    _SendMessage('images.get', SessionID=sessionid, AlbumID=albumid))
  return [long(image('id')) for image in r.Images[:]]


def KeywordsForImage(sessionid, imageid):
  """Returns the list of all keywords for the given image.
  """
  r = xmltramp.seed(_SendMessage(
    'images.getInfo', SessionID=sessionid, ImageID=imageid))
  raw_keywords = str(r.Info.Image.Keywords)
  # Clean up smugmug's bad escaping of previous keyworder runs.
  # The keyword list from such runs will look like:
  #   \"foo\" \"bar baz\"
  raw_keywords = raw_keywords.replace(r'\"', '"')
  reader = csv.reader([raw_keywords], delimiter=' ')
  keywords = []
  for row in reader:
    keywords += row
  return keywords


def CreateMappings(sessionid):
  """Retrieves keyword information for all images.

  Returns: (m, n) where
    m, dict: keyword -> [image ids]
    n, dict: image_id -> [keywords]
  """
  albumids = GetAlbumIds(sessionid)
  imageids = []
  for albumid in albumids:
    imageids += GetImageIds(sessionid, albumid)
  keyword_to_image = {}
  image_to_keyword = {}
  for imageid in imageids:
    keywords = KeywordsForImage(sessionid, imageid)
    if keywords:
      image_to_keyword[imageid] = keywords
    for keyword in keywords:
      keyword_to_image.setdefault(keyword, []).append(imageid)
  return keyword_to_image, image_to_keyword


def NewKeywords(old_to_new, keyword_to_image, image_to_keyword):
  """Returns a list of images with their new keywords.

  Args:
    old_to_new: iterable of (old_keyword, new_keyword) pairs.
    keyword_to_image, dict: keyword -> [image ids]
    image_to_keyword, dict: image_id -> [keywords]

  Returns: List of (imageid, [keywords]).  Only returns images
    whose keywords have changed.
  """
  image_to_keyword = dict(image_to_keyword)  # Don't change the argument.
  changed = {}
  for (old, new) in old_to_new:
    try:
      affected_images = keyword_to_image[old]
    except KeyError:
      continue
    for imageid in affected_images:
      old_keywords = [k for k in image_to_keyword[imageid] if k != old]
      new_keywords = old_keywords + [new]
      image_to_keyword[imageid] = new_keywords
      changed[imageid] = new_keywords
  return changed.items()


def ParseKeywordChanges(s):
  """Parses a set of desired keyword changes from the commandline
  argument.  Returns an iterable of (old, new) pairs.
  """
  pairs = s.split(',')
  return (p.split(':') for p in pairs)


def UpdateImageKeywords(sessionid, imageid, old_keywords, new_keywords):
  """Sends a command to smugmug to update the keywords for the given
  image from old_keywords to new_keywords.  old_keywords and new_keywords
  should both be iterables of keyword strings.
  """
  oldkeywordstr = ' '.join(['"%s"' % s for s in old_keywords])
  newkeywordstr = ' '.join(['"%s"' % s for s in new_keywords])
  print '*** Updating image %d.\nOld keywords: %s\nNew keywords: %s' % (
    imageid, oldkeywordstr, newkeywordstr)
  r = xmltramp.seed(
    _SendMessage('images.changeSettings',
                 SessionID=sessionid, ImageID=imageid, Keywords=newkeywordstr))


def main(argv):
  p = optparse.OptionParser(usage='%prog --email=... --password=... --keywords=old1:new1,old2:new2')
  p.add_option('--email', help='Email address registered with smugmug.')
  p.add_option('--password', help='Your smugmug password')
  p.add_option('--keywords',
               help=('Comma-separated list of old:new keywords.  '
                     'Example: foo:bar,high:low'))
  (options, args) = p.parse_args(argv[1:])
  if (options.email is None or options.password is None
      or options.keywords is None or args):
    p.print_help()
    return 1

  old_to_new = ParseKeywordChanges(options.keywords)
  sessionid = Login(options.email, options.password)
  keyword_to_image, image_to_keyword = CreateMappings(sessionid)

  deltas = NewKeywords(old_to_new, keyword_to_image, image_to_keyword)
  for (imageid, new_keywords) in deltas:
    old_keywords = image_to_keyword[imageid]
    UpdateImageKeywords(sessionid, imageid, old_keywords, new_keywords)
  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv))
