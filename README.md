# mc-recipe-img <!-- omit in toc -->

A library and command-line tool for generating images of Minecraft recipes (crafting, smelting,
etc.) from the JSON files of a datapack.

- [Datapack format compatibility](#datapack-format-compatibility)
- [Usage: Setup](#usage-setup)
- [Usage: Creating images](#usage-creating-images)
  - [CLI Options](#cli-options)
- [Usage: Environment variables \& configuration](#usage-environment-variables--configuration)

## Datapack format compatibility

Any pack format not listed below has not been thoroughly tested and may or may not work with the
script.

- ✅ = Works as intended
- ❔ = Works partially or requires a workaround (explained in notes)
- ❌ = Does not work (may be fixed in future)

|Format|Status|Notes|
|:-----:|:----:|-----|
|94.1|✅||

## Usage: Setup

Use `pip` to install this package to your system or virtual enviornment.

```bash
pip install git+https://github.com/svioletg/mc-recipe-img.git
```

Once installed, run `mc-recipe-img --help` to see all available commands and arguments.

## Usage: Creating images

Examples

```bash
mc-recipe-img run --pack=mypack --textures=mc-resources/ --out=images/
```

```bash
mc-recipe-img run -i mypack -t mc-resources/ -o images/
```

```bash
mc-recipe-img run -i mypack -t 1.21.11 -o images/
```

### CLI Options

|Name|Description|
|----|-----------|
|`--pack/-i`|The path to the datapack to search for recipes in, i.e. the directory which holds the `data` subdirectory.|
|`--textures/-t`|The path to a directory holding extracted assets from a Minecraft JAR (the final component of this path should be `assets`), or a Minecraft version to automatically extract the needed assets from. The latter will use the JAR found in your installation's `versions` directory, so you need to have run this version of the game at least once for this to work. This value can be given multiple times in order of highest to lowest priority to specify fallback values.|
|`--out/-o`|Output directory to save recipe images to. Recipes will be saved in this directory under `<namespace>/<recipe>.png` for each namespace folder found in the given datapack path.|

## Usage: Environment variables & configuration

The script will sometimes need to check your Minecraft installation directory for things like
installed version JAR files. In this case, the `MC_HOME` environment variable will be checked
first, then the [default location for your system](https://minecraft.wiki/w/.minecraft#Location)
is used instead.

Some CLI options can be set through environment variables, in which case the corresponding option
becomes optional when running the command.

|Option|Variable|Notes|
|------|--------|-----|
|`--pack/-i`|`DATAPACK_DIR`||
|`--textures/-t`|`MC_ASSETS_SRC`|Sources must be separated by `:`, e.g. `local-resource-pack/assets:1.21.11`|
