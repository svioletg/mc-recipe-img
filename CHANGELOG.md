# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0]

### Added

- CLI commands
  - `run`: Runs the main image generation script
  - `cache`
    - `show`: Prints the script's cache directory
    - `clear`: Removes all contents of the script's cache directory
- Added `cli` module
- Added `core` module
- Added `mc` module
- Added `util` module
- Added support for 8 recipe types
  - `blasting`
  - `crafting_shaped`
  - `crafting_shapeless`
  - `crafting_transmute`
  - `smelting`
  - `smithing_transform`
  - `smithing_trim`
  - `smoking`
