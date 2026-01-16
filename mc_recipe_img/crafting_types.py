from dataclasses import dataclass
from pathlib import Path
from typing import Self, TypedDict

from mc_recipe_img import ASSETS_DIR


class ItemSlot(TypedDict):
    pos: tuple[int, int]
    item: str | None

@dataclass
class CraftingInterface:
    base_img: Path
    input_slots: dict[str, ItemSlot]
    output_slots: dict[str, ItemSlot]

    @classmethod
    def crafting_table(cls) -> Self:
        return cls(ASSETS_DIR / 'base_crafting_image.png',
            input_slots={
                'top-left'      : {'pos': (30, 17), 'item': None},
                'top-center'    : {'pos': (48, 17), 'item': None},
                'top-right'     : {'pos': (66, 17), 'item': None},
                'middle-left'   : {'pos': (30, 35), 'item': None},
                'middle-center' : {'pos': (48, 35), 'item': None},
                'middle-right'  : {'pos': (66, 35), 'item': None},
                'bottom-left'   : {'pos': (30, 53), 'item': None},
                'bottom-center' : {'pos': (48, 53), 'item': None},
                'bottom-right'  : {'pos': (66, 53), 'item': None},
            },
            output_slots={
                'result': {'pos': (124, 35), 'item': None},
            },
        )

    @classmethod
    def furnace(cls) -> Self:
        return cls(ASSETS_DIR / 'base_furnace.png',
            input_slots={
                'ingredient': {'pos': (56, 17), 'item': None},
                'fuel': {'pos': (56, 53), 'item': None},
            },
            output_slots={
                'result': {'pos': (116, 35), 'item': None},
            },
        )

    @classmethod
    def blast_furnace(cls) -> Self:
        inst = cls.furnace()
        inst.base_img = ASSETS_DIR / 'base_blast_furnace.png'
        return inst

    @classmethod
    def smoker(cls) -> Self:
        inst = cls.furnace()
        inst.base_img = ASSETS_DIR / 'base_smoker.png'
        return inst

    @classmethod
    def smithing_table(cls) -> Self:
        return cls(ASSETS_DIR / 'base_smithing_table.png',
            input_slots={
                'template': {'pos': (8, 48), 'item': None},
                'tool': {'pos': (26, 48), 'item': None},
                'material': {'pos': (44, 48), 'item': None},
            },
            output_slots={
                'result': {'pos': (98, 48), 'item': None},
            },
        )

    @classmethod
    def brewing_stand(cls) -> Self:
        return cls(ASSETS_DIR / 'base_brewing_stand.png',
            input_slots={
                'fuel': {'pos': (17, 17), 'item': None},
                'ingredient': {'pos': (79, 17), 'item': None},
            },
            output_slots={
                'left': {'pos': (56, 51), 'item': None},
                'center': {'pos': (56, 51), 'item': None},
                'right': {'pos': (56, 51), 'item': None},
            },
        )
