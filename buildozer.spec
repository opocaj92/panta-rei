[app]
title = Panta Rei
package.name = pantarei
# Replace this identifier before distributing the application publicly.
package.domain = org.pantarei
source.dir = .
source.include_exts = py,json,png,jpg,jpeg,webp,wav,ogg,mp3,ttf,otf
source.exclude_dirs = tests,.github,__pycache__,.venv,venv,dist,build
version = 0.8.5
# Android compilation requires a compatible pygame recipe. See ANDROID_BUILD.md.
requirements = hostpython3==3.10.12,python3==3.10.12,pygame,pyjnius
orientation = landscape
fullscreen = 1
icon.filename = assets/icons/panta_rei_android.png
android.archs = arm64-v8a
android.minapi = 26
android.api = 35
android.accept_sdk_license = True
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
