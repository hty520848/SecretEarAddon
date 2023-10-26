'''
Copyright (C) 2015 Pistiwique, Pitiwazou

Created by Pistiwique, Pitiwazou
 
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
 
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
 
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import os
import bpy
import bpy.utils.previews

icon_collection = {}
icons_loaded = False


def load_icons():
    global icon_collection
    global icons_loaded

    if icons_loaded: return icon_collection["main"]

    custom_icons = bpy.utils.previews.new()

    icons_dir = os.path.join(os.path.dirname(__file__))

    # modals
    custom_icons.load("icon_rebool", os.path.join(icons_dir, "rebool.png"), 'IMAGE')
    custom_icons.load("icon_reset", os.path.join(icons_dir, "reset.png"), 'IMAGE')
    custom_icons.load("icon_backup", os.path.join(icons_dir, "backup.png"), 'IMAGE')
    custom_icons.load("icon_forward", os.path.join(icons_dir, "forward.png"), 'IMAGE')
    custom_icons.load("icon_grid", os.path.join(icons_dir, "grid.png"), 'IMAGE')
    custom_icons.load("icon_link", os.path.join(icons_dir, "link.png"), 'IMAGE')
    custom_icons.load("icon_open", os.path.join(icons_dir, "open.png"), 'IMAGE')
    custom_icons.load("icon_ruler", os.path.join(icons_dir, "ruler.png"), 'IMAGE')
    custom_icons.load("icon_save", os.path.join(icons_dir, "save.png"), 'IMAGE')
    

    custom_icons.load("icon_transparency1", os.path.join(icons_dir, "transparency1.png"), 'IMAGE')
    custom_icons.load("icon_transparency2", os.path.join(icons_dir, "transparency2.png"), 'IMAGE')
    custom_icons.load("icon_transparency3", os.path.join(icons_dir, "transparency3.png"), 'IMAGE')
    custom_icons.load("icon_viewShift", os.path.join(icons_dir, "viewShift.png"), 'IMAGE')




    icon_collection["main"] = custom_icons
    icons_loaded = True

    return icon_collection["main"]


def clear_icons():
    global icons_loaded
    for icon in icon_collection.values():
        bpy.utils.previews.remove(icon)
    icon_collection.clear()
    icons_loaded = False