
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

# Android options must be in [app].
android.minapi = 23
android.api = 33
android.ndk = 25b
android.archs = arm64-v8a
android.permissions = INTERNET

# GitHub Actions prepares this SDK directory before Buildozer starts. Buildozer
# reads android.sdk_path from the spec; ANDROIDSDK alone is not the selector.
android.sdk_path = .android-sdk
android.skip_update = True
android.accept_sdk_license = True

# Keep the Android SDK/NDK and Python recipes on the versions supported by this
# p4a release.
p4a.branch = v2024.01.21
p4a.source_dir = .p4a

presplash.filename =
icon.filename =
orientation = landscape
fullscreen = 1
android.presplash_color = #08111F
android.apptheme = "@android:style/Theme.Material.NoActionBar"
services =

[buildozer]
log_level = 2
warn_on_root = 1
