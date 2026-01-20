# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- CLI options
  - Added `--log-file` option to save debug logs to a given file
    - File will be overwritten, option must go before subcommands like `run`
- Added private attribute `mc.Datapack._texture_map` to cache the result of `mc.Datapack.get_texture_map()`

### Changed

- Renamed `mc.Datapack._render_recipe()` to `mc.Datapack.render_recipe()`
  - Now a public method
- Renamed `mc.Datapack._get_texture_or_cached()` to `mc.Datapack.get_loaded_texture()`
  - Now a public method
  - With the addition of the `get_texture_map()` method, this aims to make a clear distinction
    between getting the value of a key from said method (which would return the path to a texture)
    and getting an already loaded `Image.Image` object from this method
- Renamed `mc.Datapack.find_required_textures()` to `mc.Datapack.get_texture_map()`
  - Can now extract the required textures from JARs, which was
    previously only done when running the script as a command
  - No longer takes an `assets_sources` argument, instead uses the instance attribute
- `mc.Datapack.render_recipe()` and `mc.Datapack.render_recipes()` no longer take a `texture_map`
  argument

### Fixed

- Tags within tags are now fully expanded
- The result item texture in 3x3 crafting grid recipes is now positioned correctly

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
