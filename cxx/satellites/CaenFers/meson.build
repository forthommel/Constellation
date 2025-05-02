# SPDX-FileCopyrightText: 2024 DESY and the Constellation authors
# SPDX-License-Identifier: CC0-1.0

# Build satellite if option is set
if not get_option('satellite_caenfers')
  subdir_done()
endif

# Type this satellite identifies as
satellite_type = 'CaenFers'

# Source files to be compiled for this satellite
satellite_sources = files(
  'CaenFersSatellite.cpp',
)

# Additional dependencies for this satellite
janusc_sources = include_directories('/home/laurent/Downloads/Janus_5203_2.8.2_20241029_linux/src')
janusc = declare_dependency(include_directories: janusc_sources,
  compile_args: '-DFERS_5203 -Wall -Wno-write-strings -std=c++11 -Dlinux')
satellite_dependencies = [janusc]
satellite_compile_args = '-pthread -lrt'

# Add [type, sources, dependencies] to build list
satellites_to_build += [[satellite_type, satellite_sources, satellite_dependencies]]
