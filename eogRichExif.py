# thanks to author(s) of eogMetaEdit plugin

from gi.repository import GObject, Gtk, Eog
from urllib.parse import urlparse
import pyexiv2

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
		# need to track file changes in the EoG thumbview
		self.thumbview = self.window.get_thumb_view()		

		# the EogImage of the main window
		self.curImage = None
		# the EogImage selected in the thumbview
		self.thumbImage = None


#		builder = Gtk.Builder()
#		builder.add_from_file(join(self.plugin_info.get_data_dir(),\
#								"eogRichExif.glade"))
#		pluginDialog = builder.get_object('eogRichExif')
#		
#		# add dialog to the sidebar
#		Eog.Sidebar.add_page(self.sidebar,"Custom Metadata Show", pluginDialog)

#		self.metadata = pyexiv2.ImageMetadata(filePath)
#		self.metadata.read()

		self.cb_ids = {}
		self.cb_ids['selection-changed'] = {}
		self.cb_ids['selection-changed'][self.thumbview] = \
			self.thumbview.connect('selection-changed', \
				self.selection_changed_cb, self)
		
	def do_deactivate(self):
		print('The answer fell off my rooftop, woot')

	@staticmethod
	def	selection_changed_cb(thumb, self):
		print("dbg: in selection_changed_cb")
		self.curImage = self.window.get_image()
		self.thumbImage = self.thumbview.get_first_selected_image()
		Event = Gtk.get_current_event()
		
		if self.Debug:
			print('\n\nfile changed ----------------------------------------')
			print('Event: ',Event)
			if Event != None:
				print('Event type: ',Event.type)
			self.showImages()

		if Event != None and self.thumbImage == None:
			# this happens when you use the toolbar next/previous buttons as 
			# opposed to the arrow keys or clicking an icon in the thumb nav.
			# seem to be able to safely just discard it and then the various
			# new image selections work the same.
			if self.Debug:
				print('selection event received with no thumbImage.  discard!')
			return False	

		if self.thumbImage != None:		
			if self.Debug:
				print('loading thumb meta:',\
					urlparse(self.thumbImage.get_uri_for_display()).path)
		else:
			if self.Debug:
				print('no metadata to load!')
				self.showImages()
			return False

		# return False to let any other callbacks execute as well
		return False

	def showImages(self):
		'''debug function: dump the current images paths'''
		print("dbg: in showImages")
		
		if self.curImage == None:
			print('current: None')
		else:
			print('current: ',urlparse(self.curImage.get_uri_for_display()).path)
		try:
			print('win says: ',urlparse(self.window.get_image().get_uri_for_display()).path)
		except:
			print('win says:none')
		if self.thumbImage == None:	
			print('thumb: None')
		else:
			print('thumb: ',urlparse(self.thumbImage.get_uri_for_display()).path)
		try:
			print('thumb says: ',urlparse(self.thumbview.get_first_selected_image().get_uri_for_display()).path)
		except:
			print('none')
