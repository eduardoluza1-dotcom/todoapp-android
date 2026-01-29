[app]
title = TodoApp
package.name = todoapp
package.domain = org.carlos.edu
version = 0.1

source.dir = .
source.include_exts = py,kv,json,png,jpg,jpeg,ttf

requirements = python3,kivy,kivymd

orientation = portrait
fullscreen = 0
log_level = 2

# ANDROID
android.api = 33
android.minapi = 23

# Fix para não tentar build-tools 36.x
android.sdk_api = 33
android.ndk_api = 23
android.sdk_build_tools_version = 33.0.2

android.archs = arm64-v8a
android.bootstrap = sdl2
android.enable_androidx = True
android.copy_libs = 1
