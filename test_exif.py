import pyexiv2
metadata = pyexiv2.ImageMetadata('DSC_1608.JPG')
metadata.read()
metadata.exif_keys
tag = metadata['Exif.Image.DateTime']
tag.value

metadata['Exif.Photo.FNumber'].value.__float__()



