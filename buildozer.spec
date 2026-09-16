
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

# Use the Python and Kivy versions supplied and tested by the pinned p4a release.
# hostpython3 is an internal build dependency and must not be an app requirement.
requirements = python3,kivy

# Android options.
android.minapi = 24
android.api = 33
android.ndk = 25b
android.archs = arm64-v8a
android.permissions = INTERNET

# GitHub Actions prepares this SDK directory before Buildozer starts.
android.sdk_path = .android-sdk
android.skip_update = True
android.accept_sdk_license = True

# Current stable p4a release. This contains the modern installed-hostpython
# handling that avoids running build-tree Python without its extension modules.
p4a.branch = v2026.05.09
p4a.source_dir = .p4a

presplash.filename =
icon.filename =
orientation = landscape
fullscreen = 1
android.presplash_color = #08111F
android.apptheme = @android:style/Theme.Material.NoActionBar
services =

[buildozer]
log_level = 2
warn_on_root = 1
