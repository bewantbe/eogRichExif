'''
  eogRichExif

  A eog (Eye of GNOME Image Viewer) plugin which shows many Exif info in side pane.

  Thanks to the eogMetaEdit plugin.
'''

'''
  eogRichExif is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  eogRichExif is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with eogRichExif.  If not, see <http://www.gnu.org/licenses/>.
'''

from gi.repository import GObject, Gtk, Eog
from os.path import join, basename
from urllib.parse import urlparse
import xml.sax.saxutils
import pyexiv2
import math


class eogRichExif(GObject.Object, Eog.WindowActivatable):
	# Override EogWindowActivatable's window property
	# This is the EogWindow this plugin instance has been activated for
	window = GObject.property(type=Eog.Window)
	Debug = False

	def __init__(self):
#		will be execulted when activating
		GObject.Object.__init__(self)

	def do_activate(self):
		if self.Debug:
			print('The answer landed on my rooftop, whoa')
		
		# get sidebar
		self.sidebar = self.window.get_sidebar()
		# need to track file changes in the EoG thumbview (any better idea?)
		self.thumbview = self.window.get_thumb_view()		
		# the EogImage selected in the thumbview
		self.thumbImage = None
		self.cb_ids = {}
		self.plugin_window = None

		# Python and GTK
		# https://python-gtk-3-tutorial.readthedocs.org/en/latest/introduction.html
		# http://www.pygtk.org/pygtk2tutorial/sec-Notebooks.html
		# http://gnipsel.com/glade/
		builder = Gtk.Builder()
		builder.add_from_file(join(self.plugin_info.get_data_dir(),\
								"eogRichExif.glade"))
		self.plugin_window = builder.get_object('eogRichExif')
		self.label_exif = builder.get_object('label_exif')

		# add dialog to the sidebar
		Eog.Sidebar.add_page(self.sidebar, "RichExif", self.plugin_window)

		self.cb_ids['selection-changed'] = {}
		self.cb_ids['selection-changed'][self.thumbview] = \
			self.thumbview.connect('selection-changed', \
				self.selection_changed_cb, self)
		
	def do_deactivate(self):
		'''remove all the callbacks stored in dict self.cb_ids '''
		if self.Debug:
			print('The answer fell off my rooftop, woot')
		
		for S in self.cb_ids:
			for W, id in self.cb_ids[S].items():
				W.disconnect(id)

	# Load metadata
	@staticmethod
	def	selection_changed_cb(thumb, self):
		if self.Debug:
			print("--- dbg: in selection_changed_cb ---")

		# Get file path
		self.thumbImage = self.thumbview.get_first_selected_image()
		Event = Gtk.get_current_event()
		self.filePath = None
		self.fileURL = None
		if self.thumbImage != None:		
			self.fileURL = self.thumbImage.get_uri_for_display()
			# https://docs.python.org/2/library/urlparse.html
			self.filePath = urlparse(self.fileURL).path
			if self.Debug:
				print('loading thumb meta: \n  ', self.filePath, '\n  URL: ', self.fileURL)
		else:
			if self.Debug:
				print('Fail to load metadata!')
			return False

		# Read metadata
		# http://python3-exiv2.readthedocs.org/en/latest/tutorial.html
		self.metadata = pyexiv2.ImageMetadata(self.filePath)
		try:
			self.metadata.read()
		except:
			self.metadata = None
			self.label_exif.set_markup("Cannot read metadata.\n self.filePath=%s" % self.filePath)
			return

#		try:
		self.set_info()
#		except KeyError as e:
#			self.label_exif.set_markup("Metadata incomplete?\n  Error: {0}\n".format(e))

		# return False to let any other callbacks execute as well
		return False

	def set_info(self):

		def is_integer(a):
			if math.fabs(a-math.floor(a+0.5)) < 1e-5:
				return True
			else:
				return False

		st_markup = '%s\n' % self.filePath;

		if 'Exif.Image.Model' in self.metadata:
			image_make = ''
			if 'Exif.Image.Make' in self.metadata:
				image_make = xml.sax.saxutils.escape(self.metadata['Exif.Image.Make'].value) + '\n '
			image_model = xml.sax.saxutils.escape(self.metadata['Exif.Image.Model'].value)
			st_markup += '<b>Camera:</b>\n %s%s\n' % (image_make, image_model)

		# Time
		NO_TIME = '0000:00:00 00:00:00'
		s_time_tag = [
		[NO_TIME, 'Exif.Image.DateTime',          'DateTime'],
		[NO_TIME, 'Exif.Image.DateTimeOriginal',  'DateTimeOriginal'],
		[NO_TIME, 'Exif.Photo.DateTimeOriginal',  'DateTimeOriginal'],
		[NO_TIME, 'Exif.Image.DateTimeDigitized', 'DateTimeDigitized'],
		[NO_TIME, 'Exif.Photo.DateTimeDigitized', 'DateTimeDigitized']]
		for idx, ttag in enumerate(s_time_tag):
			if ttag[1] in self.metadata:
				s_time_tag[idx][0] = self.metadata[ttag[1]].value

		# remove nonsence data
		s_time_tag = list(filter(lambda x: x[0]!=NO_TIME, s_time_tag))

		if len(set([r[0] for r in s_time_tag])) > 1:  # time are different
			for ttag in s_time_tag:
				st_markup += '<b>%s:</b>\n<tt> %s</tt>\n' % (ttag[2], ttag[0].strftime('%Y-%m-%d %H:%M:%S'))
		elif len(s_time_tag) == 0:
			st_markup += '<b>DateTime:</b>\n<tt> ??</tt>\n'
		else: # unique time
			st_markup += '<b>DateTime:</b>\n<tt> %s</tt>\n' % (s_time_tag[0][0].strftime('%Y-%m-%d %H:%M:%S'))

		# ExposureTime
		if 'Exif.Photo.ExposureTime' in self.metadata:
			st_exposure_time = self.metadata['Exif.Photo.ExposureTime'].human_value
		else:
			st_exposure_time = '?? s'
		# FNumber
		if 'Exif.Photo.FNumber' in self.metadata:
			f_number = self.metadata['Exif.Photo.FNumber'].human_value
		elif 'Exif.Photo.ApertureValue' in self.metadata:
			f_number = self.metadata['Exif.Photo.ApertureValue'].human_value
		else:
			f_number = 'F??'
		# ISO
		iso = ''
		if 'Exif.Photo.ISOSpeedRatings' in self.metadata:
			iso = self.metadata['Exif.Photo.ISOSpeedRatings'].human_value
		else:
			if 'Exif.Nikon3.ISOSettings' in self.metadata:
				iso = self.metadata['Exif.Nikon3.ISOSettings'].human_value
			if 'Exif.NikonIi.ISO' in self.metadata:
				iso = self.metadata['Exif.NikonIi.ISO'].human_value
		
		# extra ISO
		if 'Exif.NikonIi.ISOExpansion' in self.metadata:
			iso_ext = self.metadata['Exif.NikonIi.ISOExpansion'].human_value
			if 'off' in iso_ext.lower():
				iso += '' # do nothing
			else:
				iso += '(%s)' % iso_ext

		st_markup += '<b>Exposure:</b>\n'
		st_markup += '<tt> %s, %s</tt>\n' % (st_exposure_time, f_number)
		st_markup += '<tt> ISO %s</tt>\n' % (iso)


		# Focal Length
		if 'Exif.Photo.FocalLength' in self.metadata:
			st_focal_length = "%.1f mm" % self.metadata['Exif.Photo.FocalLength'].value.__float__()
		else:
			st_focal_length = "?? mm"
		if 'Exif.Photo.FocalLengthIn35mmFilm' in self.metadata:
			st_focal_length_35mm = "%.1f mm (35mm)" % self.metadata['Exif.Photo.FocalLengthIn35mmFilm'].value.__float__()
		else:
			st_focal_length_35mm = '?? mm (35mm)'
		st_markup += '<tt> %s</tt>\n' % (st_focal_length)
		st_markup += '<tt> %s</tt>\n' % (st_focal_length_35mm)

		if 'Exif.Photo.Flash' in self.metadata:
			st_markup += '<b>Flash:</b>\n'
			st_markup += ' %s\n' % self.metadata['Exif.Photo.Flash'].human_value

		def sign(a):
			return (a > 0) - (a < 0)
    
		# White Balance
		st_markup += '<b>WhiteBalance:</b>\n'
		if 'Exif.Nikon3.WhiteBalance' in self.metadata:
			wb_extra = self.metadata['Exif.Nikon3.WhiteBalance'].human_value.strip()
			if 'Exif.Nikon3.WhiteBalanceBias' in self.metadata:
				v = self.metadata['Exif.Nikon3.WhiteBalanceBias'].value
				wb_extra += ', Bias: %s:%d, %s:%d' % (('A','_','B')[sign(v[0])+1], abs(v[0]), ('M','_','G')[sign(v[1])+1], abs(v[1]))
			st_markup += ' %s\n' % wb_extra
		elif 'Exif.CanonPr.WhiteBalanceRed' in self.metadata:
			wb_extra = self.metadata['Exif.Photo.WhiteBalance'].human_value.strip()
			v_r = self.metadata['Exif.CanonPr.WhiteBalanceRed'].value
			v_b = self.metadata['Exif.CanonPr.WhiteBalanceBlue'].value
			wb_extra += ', Bias: R:%d, B:%d' % (v_r, v_b)
			# not sure the logic
			if 'Manual' in wb_extra:
				v_t = self.metadata['Exif.CanonPr.ColorTemperature'].value
				wb_extra += ', %dK' % v_t
			st_markup += ' %s\n' % wb_extra
		else:
			if 'Exif.Photo.WhiteBalance' in self.metadata:
				wb = self.metadata['Exif.Photo.WhiteBalance'].human_value
			else:
				wb = ''
			st_markup += ' %s\n' % wb

		# Focus Mode
		if 'Exif.Nikon3.Focus' in self.metadata:
			st_markup += '<b>Focus Mode:</b>\n'
			st_markup += ' %s\n' % self.metadata['Exif.Nikon3.Focus'].value.strip()
			if 'Exif.NikonAf2.ContrastDetectAF' in self.metadata:
				st_cdaf = self.metadata['Exif.NikonAf2.ContrastDetectAF'].human_value
				if 'on' in st_cdaf.lower():
					st_markup += ' ContrastDetectAF:\n   %s\n' % st_cdaf
			if 'Exif.NikonAf2.PhaseDetectAF' in self.metadata:
				st_pdaf = self.metadata['Exif.NikonAf2.PhaseDetectAF'].human_value
				if 'on' in st_pdaf.lower():
					st_markup += ' PhaseDetectAF:\n   %s\n' % st_pdaf

		if 'Exif.Sony1.FocusMode' in self.metadata:
			st_markup += '<b>Focus Mode:</b>\n'
			st_markup += ' %s\n' % self.metadata['Exif.Sony1.FocusMode'].human_value.strip()
			st_markup += ' %s\n' % self.metadata['Exif.Sony1.AFMode'].human_value.strip()

		if 'Exif.CanonCs.FocusMode' in self.metadata:
			st_markup += '<b>Focus Mode:</b>\n'
			st_markup += ' %s\n' % self.metadata['Exif.CanonCs.FocusMode'].human_value.strip()
			st_markup += ' FocusType: %s\n' % self.metadata['Exif.CanonCs.FocusType'].human_value.strip()

		st_markup += '<b>Extra settings:</b>\n'
		s_tag_name_extra = [
		('Exif.Photo.ExposureBiasValue', 'Exposure Bias Value'),
		('Exif.Photo.ExposureProgram',   'Exposure Program'),
		('Exif.Photo.MeteringMode',      'Metering Mode'),
		('Exif.Photo.SceneCaptureType',  'Scene Capture Type'),
		('Exif.Photo.ColorSpace',        'Color Space'),
		# Nikon
		('Exif.Nikon3.ActiveDLighting',       'DLighting'),
		('Exif.NikonVr.VibrationReduction',   'Vibration Reduction'),
		('Exif.Nikon3.NoiseReduction',        'Noise Reduction'),
		('Exif.Nikon3.HighISONoiseReduction', 'High ISO Noise Reduction'),
		('Exif.Nikon3.ShootingMode',          'Shooting Mode'),
		# Canon
		('Exif.CanonFi.NoiseReduction', 'Noise Reduction'),
		# Sony
		('Exif.Sony1.AutoHDR', 'Auto HDR'),
		('Exif.Sony1.LongExposureNoiseReduction', 'LongExposureNoiseReduction')
		]
		for tag_name in s_tag_name_extra:
			if tag_name[0] in self.metadata:
				st_markup += ' <i>%s:</i>\n   %s\n' % \
				(tag_name[1], self.metadata[tag_name[0]].human_value)

		st_markup += '<b>Lens:</b>\n'
		s_tag_name_lens = [
		('Exif.NikonLd3.FocalLength',   'Focal Length'),
		('Exif.NikonLd3.AFAperture',    'AFAperture'),
		('Exif.NikonLd3.FocusDistance', 'Focus Distance'),
		]
		for tag_name in s_tag_name_lens:
			if tag_name[0] in self.metadata:
				st_markup += ' <i>%s:</i> %s\n' % \
				(tag_name[1], self.metadata[tag_name[0]].human_value)

		st_markup += '<b>Lens Model:</b>\n'
		if 'Exif.Nikon3.Lens' in self.metadata:
			st_markup += ' %s\n' % self.metadata['Exif.Nikon3.Lens'].human_value
		if 'Exif.Canon.LensModel' in self.metadata:
			st_markup += ' %s\n' % self.metadata['Exif.Canon.LensModel'].human_value
		if 'Exif.Photo.LensModel' in self.metadata:
			st_markup += ' %s\n' % self.metadata['Exif.Photo.LensModel'].human_value

		if 'Exif.GPSInfo.GPSLatitudeRef' in self.metadata:
			lr = self.metadata['Exif.GPSInfo.GPSLatitudeRef'].value
			lv = self.metadata['Exif.GPSInfo.GPSLatitude'].value
			ar = self.metadata['Exif.GPSInfo.GPSLongitudeRef'].value
			av = self.metadata['Exif.GPSInfo.GPSLongitude'].value
			st_markup += '<b>GPS:</b>\n %.0f° %.0f\' %.2f" %s,\n %.0f° %.0f\' %.2f" %s,\n' % \
				(float(lv[0]), float(lv[1]), float(lv[2]), lr, \
				 float(av[0]), float(av[1]), float(av[2]), ar)
			st_markup += ' %s %s.\n' % (self.metadata['Exif.GPSInfo.GPSAltitude'].human_value,\
				self.metadata['Exif.GPSInfo.GPSAltitudeRef'].human_value)

		previews = self.metadata.previews

		st_markup += '<b>Number of thumbnails:</b>\n <tt>%d</tt>\n' % len(previews)

#		if 'NIKON' in image_make:
#			if ('Exif.Photo.UserComment' in self.metadata):
#				st_markup += '<b>UserComment:</b>\n <tt>%s</tt>\n' % self.metadata['Exif.Photo.UserComment'].human_value

		self.label_exif.set_markup(st_markup)
