# mc-recipe-img

A library and command-line tool for generating images of Minecraft recipes
(crafting, smelting, etc.) from the JSON files of a datapack.

## Usage: Setup

Use `pip` to install this package to your system or virtual enviornment.

```bash
pip install git+https://github.com/svioletg/mc-recipe-img.git
```

Once installed, run `mc-recipe-img --help` to see all available commands and arguments.

## Usage: Creating images

Examples

`mc-recipe-img run --pack=mypack --textures=mc-resources/ --out=images/`
`mc-recipe-img run -i mypack -t mc-resources/ -o images/`
`mc-recipe-img run -i mypack -t 1.21.11 -o images/`

### CLI Options

|Name|Description|
|----|-----------|
|`--pack/-i`|The path to the datapack to search for recipes in, i.e. the directory which holds the `data` subdirectory.|
|`--textures/-t`|The path to a directory holding extracted assets from a Minecraft JAR (should point to the parent `assets` directory), or a Minecraft version to automatically extract the needed assets from. The latter will use the JAR found in your installation's `versions` directory, so you need to have run this version of the game at least once for this to work.|
|`--out/-o`|Output directory to save recipe images to. Recipes will be saved in this directory under `<namespace>/<recipe>.png` for each namespace folder found in the given datapack path.|

The `MC_ASSETS_SRC` environment variable will be used if the variable is set and `--textures` is not given.
