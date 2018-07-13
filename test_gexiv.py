#!/usr/bin/python3
# https://wiki.gnome.org/Projects/gexiv2
# https://wiki.gnome.org/Projects/gexiv2/PythonSupport
# https://github.com/GNOME/gexiv2

from gi.repository import GExiv2

exif = GExiv2.Metadata('test_pic/NIKON D90.JPG')

ss=[
'Exif.Image.Model',
'Exif.Image.DateTime',
'Exif.Image.DateTimeOriginal',
'Exif.Photo.ExposureTime',
'Exif.Photo.FNumber',
'Exif.Photo.ApertureValue',
'Exif.Photo.ISOSpeedRatings',
'Exif.Nikon3.ISOSettings',
'Exif.NikonIi.ISO',
'Exif.Photo.FocalLength',
'Exif.Photo.UserComment',
'Exif.Nikon3.WhiteBalance'
]

for s in ss:
	if s in exif:
#		print '%s: %s' % (s, exif[s])
		print('%s: %s' % (s, exif.get_tag_interpreted_string(s)))
	else:
		print('%s: (not exist)' % s)

