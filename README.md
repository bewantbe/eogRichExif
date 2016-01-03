# eogRichExif
A eog (Eye of GNOME Image Viewer) plugin which shows many camera related Exif info in side pane.

To install, put these files (eogRichExif.glade, eogRichExif.py, eogRichExif.plugin) in

  $XDG_DATA_HOME/eog/plugins/eogRichExif/

Usually default value for $XDG_DATA_HOME is $HOME/.local/share (at least for gnome 3.14)

Need to install libexiv2, python3-dev, py3exiv2(http://python3-exiv2.readthedocs.org/en/latest/index.html you will need to compile it your self).

Then enable it in eog Preferences, Plugins tab.
