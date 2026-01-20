from dataclasses import dataclass
from pathlib import Path

from mc_recipe_img import ASSETS_DIR, Point


class RecipeImageBase:
    base_path: Path = NotImplemented

@dataclass
class RecipeImageSmelting(RecipeImageBase):
    base_path: Path = ASSETS_DIR / 'base_smelting.png'

    ingredient : Point = (9, 17)
    fuel       : Point = (9, 53)
    result     : Point = (69, 35)

@dataclass
class RecipeImageBrewing(RecipeImageBase):
    base_path: Path = ASSETS_DIR / 'base_brewing.png'

    fuel       : Point = (6, 17)
    ingredient : Point = (68, 17)
    results    : tuple[Point, ...] = ((45, 51), (68, 58), (91, 51))

@dataclass
class RecipeImageCrafting2x2(RecipeImageBase):
    base_path: Path = ASSETS_DIR / 'base_crafting_2x2.png'

    inputs: tuple[tuple[Point, Point], ...] = (((12, 18), (30, 18)), ((12, 36), (30, 36)))
    inputs_shapeless: tuple[Point, ...] = tuple(j for i in inputs for j in i)
    result: Point = (68, 28)

@dataclass
class RecipeImageCrafting3x3(RecipeImageBase):
    base_path: Path = ASSETS_DIR / 'base_crafting_3x3.png'

    inputs: tuple[tuple[Point, Point, Point], ...] = (
        ((15, 17), (33, 17), (51, 17)),
        ((15, 35), (33, 35), (51, 35)),
        ((15, 53), (33, 53), (51, 53)),
    )
    inputs_shapeless: tuple[Point, ...] = tuple(j for i in inputs for j in i)
    result: Point = (109, 35)

@dataclass
class RecipeImageSmithing(RecipeImageBase):
    base_path: Path = ASSETS_DIR / 'base_smithing.png'

    template : Point = (8, 48)
    base     : Point = (26, 48)
    addition : Point = (44, 48)
    result   : Point = (98, 48)

BLASTING        = RecipeImageSmelting(base_path=ASSETS_DIR / 'base_blasting.png')
BREWING         = RecipeImageBrewing()
CRAFTING_GRID_2 = RecipeImageCrafting2x2()
CRAFTING_GRID_3 = RecipeImageCrafting3x3()
SMELTING        = RecipeImageSmelting()
SMITHING        = RecipeImageSmithing()
SMOKING         = RecipeImageSmelting(base_path=ASSETS_DIR / 'base_smoking.png')
