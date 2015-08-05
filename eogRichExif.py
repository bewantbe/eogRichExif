# thanks to author(s) of eogMetaEdit plugin

from gi.repository import GObject, Gtk, Eog
from os.path import join, basename
from urllib.parse import urlparse
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
				print('no metadata to load!')
			return False

		# Read metadata
		# http://python3-exiv2.readthedocs.org/en/latest/tutorial.html
		self.metadata = pyexiv2.ImageMetadata(filePath)
		try:
			self.metadata.read()
		except:
			self.metadata = None
			print("Cannot read metadata.")
			return

#		self.set_info()
		try:
			self.set_info()
		except:
			self.label_exif.set_markup("Metadata incomplete.")

		# return False to let any other callbacks execute as well
		return False

	def set_info(self):

		def is_integer(a):
			if math.fabs(a-math.floor(a+0.5)) < 1e-5:
				return True
			else:
				return False
		self.metadata_keys = self.metadata.exif_keys + self.metadata.iptc_keys + \
							self.metadata.xmp_keys

		st_markup = '';
		if 'Exif.Image.DateTime' in self.metadata:
			time_iso = self.metadata['Exif.Image.DateTime'].value.strftime('%Y-%m-%d %H:%M:%S')
			st_markup += '<b>Image.DateTime:</b>\n<tt> %s</tt>\n' % time_iso

		image_model = self.metadata['Exif.Image.Model'].value
		st_markup += '<b>Camera:</b>\n %s\n' % image_model

		# ExposureTime
		st_exposure_time = self.metadata['Exif.Photo.ExposureTime'].human_value
		# FNumber
		f_number = self.metadata['Exif.Photo.FNumber'].human_value
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
		st_focal_length = "%.1f mm" % self.metadata['Exif.Photo.FocalLength'].value.__float__()
		st_focal_length_35mm = "%.1f mm (35mm film)" % self.metadata['Exif.Photo.FocalLengthIn35mmFilm'].value.__float__()
		st_markup += '<tt> %s, %s</tt>\n' % (st_focal_length, st_focal_length_35mm)

		# White Balance
		st_markup += '<b>WhiteBalance:</b>\n'
		wb = self.metadata['Exif.Photo.WhiteBalance'].human_value
		if (wb.lower() == 'auto') and ('Exif.Nikon3.WhiteBalance' in self.metadata):
			wb_extra = self.metadata['Exif.Nikon3.WhiteBalance'].human_value.strip()
			v = self.metadata['Exif.Nikon3.WhiteBalanceBias'].value
			wb_extra += ', Bias: R% d, B% d' % (v[0], v[1])
			st_markup += ' %s\n' % wb_extra
		else:
			st_markup += ' %s\n' % wb

		if 'Exif.Nikon3.Focus' in self.metadata:
			st_markup += '<b>Focus Mode:</b>\n'
			st_markup += ' %s\n' % self.metadata['Exif.Nikon3.Focus'].value.strip()
			st_cdaf = self.metadata['Exif.NikonAf2.ContrastDetectAF'].human_value
			if 'on' in st_cdaf.lower():
				st_markup += ' ContrastDetectAF: %s\n' % st_cdaf
			st_pdaf = self.metadata['Exif.NikonAf2.PhaseDetectAF'].human_value
			if 'on' in st_pdaf.lower():
				st_markup += ' PhaseDetectAF: %s\n' % st_pdaf

		st_markup += '<b>Extra settings:</b>\n'
		if 'Exif.Photo.ExposureBiasValue' in self.metadata:
			st_markup += ' Exposure Bias Value: %s\n' % self.metadata['Exif.Photo.ExposureBiasValue'].human_value
		if 'Exif.Photo.ExposureProgram' in self.metadata:
			st_markup += ' Exposure Program: %s\n' % self.metadata['Exif.Photo.ExposureProgram'].human_value
		if 'Exif.Photo.MeteringMode' in self.metadata:
			st_markup += ' Metering Mode: %s\n' % self.metadata['Exif.Photo.MeteringMode'].human_value
		if 'Exif.Photo.SceneCaptureType' in self.metadata:
			st_markup += ' Scene Capture Type: %s\n' % self.metadata['Exif.Photo.SceneCaptureType'].human_value
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

		previews = self.metadata.previews

		st_markup += '<b>Number of thumbnails:</b>\n <tt>%d</tt>\n' % len(previews)

		self.label_exif.set_markup(st_markup)
