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
	Debug = True

	def __init__(self):
#		will be execulted when activating
		GObject.Object.__init__(self)

	def do_activate(self):
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
		print('The answer fell off my rooftop, woot')
		
		for S in self.cb_ids:
			for W, id in self.cb_ids[S].items():
				W.disconnect(id)

	# Load metadata
	@staticmethod
	def	selection_changed_cb(thumb, self):
		print("--- dbg: in selection_changed_cb ---")

		# Get file path
		self.thumbImage = self.thumbview.get_first_selected_image()
		Event = Gtk.get_current_event()
		filePath = None
		fileURL = None
		if self.thumbImage != None:		
			if self.Debug:
				fileURL = self.thumbImage.get_uri_for_display()
				# https://docs.python.org/2/library/urlparse.html
				filePath = urlparse(fileURL).path
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
		exposure_time = self.metadata['Exif.Photo.ExposureTime'].value.__float__()
		if exposure_time>1:
			if is_integer(1.0/exposure_time):
				st_exposure_time = '%.0f s' % exposure_time
			else:
				st_exposure_time = '%.1f s' % exposure_time
		else:
			if is_integer(1.0/exposure_time):
				st_exposure_time = '1/%.0f s' % (1.0/exposure_time)
			else:
				st_exposure_time = '1/%.1f s' % (1.0/exposure_time)
		# FNumber
		f_number = self.metadata['Exif.Photo.FNumber'].human_value
		
		# ISO
		iso = self.metadata['Exif.Photo.ISOSpeedRatings'].value
		
		st_markup += '<b>Exposure:</b>\n<tt> %s, %s, ISO%d</tt>\n' % \
			(st_exposure_time, f_number, iso)
		# extra ISO
		if 'Exif.NikonIi.ISOExpansion' in self.metadata:
			st_markup += 'ISOExpansion:<tt> %d</tt>\n' % \
			    self.metadata['Exif.NikonIi.ISOExpansion'].value
		
		# Focal Length
		st_focal_length = "%.1f mm" % self.metadata['Exif.Photo.FocalLength'].value.__float__()
		st_focal_length_35mm = "%.1f mm (35mm film)" % self.metadata['Exif.Photo.FocalLengthIn35mmFilm'].value.__float__()
		st_markup += '<tt> %s, %s</tt>\n' % (st_focal_length, st_focal_length_35mm)

		# White Balance
		wb = self.metadata['Exif.NikonIi.ISOExpansion'].human_value

		previews = self.metadata.previews
		print('Number of thumbnails: ', len(previews))

		st_markup += '<b>Number of thumbnails:</b>\n <tt>%d</tt>\n' % len(previews)

		self.label_exif.set_markup(st_markup)
