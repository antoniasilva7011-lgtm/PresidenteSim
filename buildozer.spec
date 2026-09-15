
[app]

# (str) Title of your application
title = Presidente Simulator

# (str) Package name
package.name = presidentesimulator

# (str) Package domain (needed for android/ios packaging)
package.domain = com.fellipe

# (str) Source code where main.py live
source.dir = .

# (str) List of source files to include
source.include_exts = py,json,png,jpg,kv,atlas

# (str) Application version
version = 0.1.0

# (str) Supported requirements
requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.0
# (str) Presplash of the application
presplash.filename =

# (str) Icon of the application
icon.filename =

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = landscape

# (str) List of service to declare
services =

#
# OSX Specific
#

[buildozer]

# (str) log level (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (str) warn on root (0 = False, 1 = True)
warn_on_root = 1

# (str) path to build artifacts
# build_dir = .buildozer

# (str) default output directory
# bin_dir = ./bin

# (str) Build mode used by default
# android.debug or android.release
# target = android debug

[app:android]

# (str) Minimum API version
android.minapi = 23

# (str) Android API version
android.api = 35

# (str) Android NDK version
android.ndk = 27c

# (str) Android architecture to build for
android.archs = arm64-v8a

# (bool) Fullscreen
fullscreen = 1

# (str) Presplash background color (for Android toolchain)
android.presplash_color = #08111F

# (str) Android app theme, one of the themes from Android SDK
android.apptheme = "@android:style/Theme.Material.NoActionBar"

# (str) Android permissions
android.permissions = INTERNET

# (str) Python-for-Android branch to use
p4a.branch = master

[app:ios]
# iOS is not a target for this V0.1.
