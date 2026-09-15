
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

# Android options must be in [app]. Buildozer 1.5.0 reads the target settings
# from this section; putting them in [app:android] leaves p4a using defaults.
android.minapi = 23
android.api = 35
android.ndk = 27c
android.archs = arm64-v8a
android.permissions = INTERNET

# Pin p4a instead of following its moving master branch. This release supports
# the Python/Kivy combination above and makes the Android toolchain repeatable.
p4a.branch = v2024.01.21
# (str) Presplash of the application
presplash.filename =

# (str) Icon of the application
icon.filename =

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = landscape

# (bool) Fullscreen
fullscreen = 1

# (str) Presplash background color (for Android toolchain)
android.presplash_color = #08111F

# (str) Android app theme, one of the themes from Android SDK
android.apptheme = "@android:style/Theme.Material.NoActionBar"

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
