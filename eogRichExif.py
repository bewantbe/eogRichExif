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
		Eog.Sidebar.add_page(self.sidebar, "Custom Metadata Show", self.plugin_window)

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
		filePath = None
		fileURL = None
		if self.thumbImage != None:		
			fileURL = self.thumbImage.get_uri_for_display()
			# https://docs.python.org/2/library/urlparse.html
			filePath = urlparse(fileURL).path
			if self.Debug:
				print('loading thumb meta: \n  ', filePath, '\n  URL: ', fileURL)
		else:
			if self.Debug:
				print('Fail to load metadata!')
			return False

		# Read metadata
		# http://python3-exiv2.readthedocs.org/en/latest/tutorial.html
		self.metadata = pyexiv2.ImageMetadata(filePath)
		try:
			self.metadata.read()
		except:
			self.metadata = None
			self.label_exif.set_markup("Cannot read metadata.\n filePath=%s" % filePath)
			return

		self.set_info()
#		try:
#			self.set_info()
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

		st_markup = '';
		if 'Exif.Image.DateTime' in self.metadata:
			if self.metadata['Exif.Image.DateTime'].value != '0000:00:00 00:00:00':
				time_iso = self.metadata['Exif.Image.DateTime'].value.strftime('%Y-%m-%d %H:%M:%S')
			else:
				time_iso = ''
			st_markup += '<b>Image.DateTime:</b>\n<tt> %s</tt>\n' % time_iso

		image_model = xml.sax.saxutils.escape(self.metadata['Exif.Image.Model'].value)
		st_markup += '<b>Camera:</b>\n %s\n' % image_model

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
		st_markup += '<b>Exposure:</b>\n'
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

		st_markup += '<tt> %s, %s, ISO %s</tt>\n' % \
			(st_exposure_time, f_number, iso)

		
		# Focal Length
		if 'Exif.Photo.FocalLength' in self.metadata:
			st_focal_length = "%.1f mm" % self.metadata['Exif.Photo.FocalLength'].value.__float__()
		else:
			st_focal_length = "?? mm"
		if 'Exif.Photo.FocalLengthIn35mmFilm' in self.metadata:
			st_focal_length_35mm = "%.1f mm (35mm film)" % self.metadata['Exif.Photo.FocalLengthIn35mmFilm'].value.__float__()
		else:
			st_focal_length_35mm = '?? mm (35mm film)'
		st_markup += '<tt> %s, %s</tt>\n' % (st_focal_length, st_focal_length_35mm)

		# White Balance
		st_markup += '<b>WhiteBalance:</b>\n'
		if 'Exif.Nikon3.WhiteBalance' in self.metadata:
			wb_extra = self.metadata['Exif.Nikon3.WhiteBalance'].human_value.strip()
			if 'Exif.Nikon3.WhiteBalanceBias' in self.metadata:
				v = self.metadata['Exif.Nikon3.WhiteBalanceBias'].value
				wb_extra += ', Bias: R:%d, B:%d' % (v[0], v[1])
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

		if 'Exif.Nikon3.Focus' in self.metadata:
			st_markup += '<b>Focus Mode:</b>\n'
			st_markup += ' %s\n' % self.metadata['Exif.Nikon3.Focus'].value.strip()
			if 'Exif.NikonAf2.ContrastDetectAF' in self.metadata:
				st_cdaf = self.metadata['Exif.NikonAf2.ContrastDetectAF'].human_value
				if 'on' in st_cdaf.lower():
					st_markup += ' ContrastDetectAF: %s\n' % st_cdaf
			if 'Exif.NikonAf2.PhaseDetectAF' in self.metadata:
				st_pdaf = self.metadata['Exif.NikonAf2.PhaseDetectAF'].human_value
				if 'on' in st_pdaf.lower():
					st_markup += ' PhaseDetectAF: %s\n' % st_pdaf

		if 'Exif.Sony1.FocusMode' in self.metadata:
			st_markup += '<b>Focus Mode:</b>\n'
			st_markup += ' %s\n' % self.metadata['Exif.Sony1.FocusMode'].human_value.strip()
			st_markup += ' %s\n' % self.metadata['Exif.Sony1.AFMode'].human_value.strip()

		if 'Exif.CanonCs.FocusMode' in self.metadata:
			st_markup += '<b>Focus Mode:</b>\n'
			st_markup += ' %s\n' % self.metadata['Exif.CanonCs.FocusMode'].human_value.strip()
			st_markup += ' FocusType: %s\n' % self.metadata['Exif.CanonCs.FocusType'].human_value.strip()

		st_markup += '<b>Extra settings:</b>\n'
		if 'Exif.Photo.ExposureBiasValue' in self.metadata:
			st_markup += ' Exposure Bias Value: %s\n' % self.metadata['Exif.Photo.ExposureBiasValue'].human_value
		if 'Exif.Photo.ExposureProgram' in self.metadata:
			st_markup += ' Exposure Program: %s\n' % self.metadata['Exif.Photo.ExposureProgram'].human_value
		if 'Exif.Photo.MeteringMode' in self.metadata:
			st_markup += ' Metering Mode:\n  %s\n' % self.metadata['Exif.Photo.MeteringMode'].human_value
		if 'Exif.Photo.SceneCaptureType' in self.metadata:
			st_markup += ' Scene Capture Type:\n  %s\n' % self.metadata['Exif.Photo.SceneCaptureType'].human_value

		# Nikon
		if 'Exif.Nikon3.ActiveDLighting' in self.metadata:
			st_markup += ' DLighting: %s\n' % self.metadata['Exif.Nikon3.ActiveDLighting'].human_value
		if 'Exif.NikonVr.VibrationReduction' in self.metadata:
			st_markup += ' Vibration Reduction: %s\n' % self.metadata['Exif.NikonVr.VibrationReduction'].human_value
		if 'Exif.Nikon3.NoiseReduction' in self.metadata:
			st_markup += ' Noise Reduction: %s\n' % self.metadata['Exif.Nikon3.NoiseReduction'].human_value
		if 'Exif.Nikon3.HighISONoiseReduction' in self.metadata:
			st_markup += ' High ISO Noise Reduction: %s\n' % self.metadata['Exif.Nikon3.HighISONoiseReduction'].human_value
		if 'Exif.Nikon3.ShootingMode' in self.metadata:
			st_markup += ' Shooting Mode: %s\n' % self.metadata['Exif.Nikon3.ShootingMode'].human_value
			
		# Canon
		if 'Exif.CanonFi.NoiseReduction' in self.metadata:
			st_markup += ' Noise Reduction: %s\n' % self.metadata['Exif.CanonFi.NoiseReduction'].human_value

		# Sony
		if 'Exif.Sony1.AutoHDR' in self.metadata:
			st_markup += ' Auto HDR: %s\n' % self.metadata['Exif.Sony1.AutoHDR'].human_value
		if 'Exif.Sony1.LongExposureNoiseReduction' in self.metadata:
			st_markup += ' LongExposureNoiseReduction: %s\n' % self.metadata['Exif.Sony1.LongExposureNoiseReduction'].human_value

		st_markup += '<b>Lens:</b>\n'
		if 'Exif.NikonLd3.FocalLength' in self.metadata:
			st_markup += ' Focal Length: %s\n' % self.metadata['Exif.NikonLd3.FocalLength'].human_value
		if 'Exif.NikonLd3.AFAperture' in self.metadata:
			st_markup += ' AFAperture: %s\n' % self.metadata['Exif.NikonLd3.AFAperture'].human_value
		if 'Exif.NikonLd3.FocusDistance' in self.metadata:
			st_markup += ' Focus Distance: %s\n' % self.metadata['Exif.NikonLd3.FocusDistance'].human_value

		st_markup += '<b>Hardware:</b>\n'
		if 'Exif.Nikon3.Lens' in self.metadata:
			st_markup += ' Lens: %s\n' % self.metadata['Exif.Nikon3.Lens'].human_value
		if 'Exif.Canon.LensModel' in self.metadata:
			st_markup += ' Lens: %s\n' % self.metadata['Exif.Canon.LensModel'].human_value
		if 'Exif.Photo.LensModel' in self.metadata:
			st_markup += ' Lens: %s\n' % self.metadata['Exif.Photo.LensModel'].human_value

		if 'Exif.GPSInfo.GPSLatitudeRef' in self.metadata:
			lr = self.metadata['Exif.GPSInfo.GPSLatitudeRef'].value
			lv = self.metadata['Exif.GPSInfo.GPSLatitude'].value
			ar = self.metadata['Exif.GPSInfo.GPSLongitudeRef'].value
			av = self.metadata['Exif.GPSInfo.GPSLongitude'].value
			st_markup += '<b>GPS:</b>\n %.0fd %.0f\' %.2f" %s,\n %.0fd %.0f\' %.2f" %s,\n' % \
				(float(lv[0]), float(lv[1]), float(lv[2]), lr, \
				 float(av[0]), float(av[1]), float(av[2]), ar)
			st_markup += ' %s %s.\n' % (self.metadata['Exif.GPSInfo.GPSAltitude'].human_value,\
			    self.metadata['Exif.GPSInfo.GPSAltitudeRef'].human_value)

		previews = self.metadata.previews

		st_markup += '<b>Number of thumbnails:</b>\n <tt>%d</tt>\n' % len(previews)

#		st_markup += '<b>UserComment:</b>\n <tt>%s</tt>\n' % len(previews)

		self.label_exif.set_markup(st_markup)
