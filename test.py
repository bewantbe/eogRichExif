# 

from gi.repository import GObject, Gtk
builder = Gtk.Builder()
builder.add_from_file('eogRichExif.glade')
plugin_window = builder.get_object('eogRichExif')

def removeAdd(widget):
	box = builder.get_object('box1')
	lb = builder.get_object('label1')
	if lb == None:
		return
	box.remove(lb)
	#box.add(label2)
	label2 = Gtk.Label()
	label2.set_text('asdfasdf')
	box.pack_start(label2, True, True, 0)

botton = Gtk.Button(label="Click Here")
botton.connect('clicked', removeAdd)
box = builder.get_object('box1')
box.pack_start(botton, True, True, 0)

win = Gtk.Window()
win.add(plugin_window)
win.connect("delete-event", Gtk.main_quit)
win.show_all()
Gtk.main()

