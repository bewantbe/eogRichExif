import pyexiv2
metadata = pyexiv2.ImageMetadata('NIKON D90.JPG')
metadata.read()
#print metadata.exif_keys
tag = metadata['Exif.Image.DateTime']
print tag.value

print metadata['Exif.Photo.FNumber'].value.__float__()
print metadata['Exif.Nikon3.Focus'].value

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
	if s in metadata:
		print '%s: %s' % (s, metadata[s].human_value)
	else:
		print '%s: (not exist)' % s

