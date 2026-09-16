
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
source.exclude_dirs = .git,.github,.p4a

# (str) Application version
version = 0.1.0

# (str) Supported requirements
# hostpython3 is an internal build dependency of the python3 recipe and is not
# an application requirement; p4a selects its matching version automatically.
requirements = python3==3.11.5,kivy==2.3.0

# Android options must be in [app]. Buildozer 1.5.0 reads the target settings
# from this section; putting them in [app:android] leaves p4a using defaults.
android.minapi = 23
android.api = 33
android.ndk = 25b
android.archs = arm64-v8a
android.permissions = INTERNET

# Keep the Android SDK/NDK and Python recipes on the versions supported by this
# p4a release instead of patching old recipes to work with a newer NDK.
p4a.branch = v2024.01.21
# The workflow prepares this exact tagged source tree.
p4a.source_dir = .p4a
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
