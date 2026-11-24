"""Original measured-looking palettes and procedural surface families.

RGB swatches are authoring sRGB. Metallic and roughness are linear fractions.
"""
# Swatch, metalness, roughness, surface family
SURFACES = {
    "steel": ("9caab2", .91, .32, "metal"),
    "dark_iron": ("505962", .84, .47, "metal"),
    "bronze": ("ac7743", .83, .39, "metal"),
    "brass": ("c49752", .87, .34, "metal"),
    "gold": ("dfb65f", .93, .28, "metal"),
    "silver": ("c3cbd0", .94, .25, "metal"),
    "ash": ("a47e50", 0, .60, "wood"),
    "dark_wood": ("554033", 0, .64, "wood"),
    "leather": ("794b35", 0, .64, "leather"),
    "rawhide": ("bd996f", 0, .67, "leather"),
    "wicker": ("b69461", 0, .70, "wood"),
    "linen": ("c4b59a", 0, .84, "cloth"),
    "wool": ("736458", 0, .91, "cloth"),
    "fur": ("75604b", 0, .95, "fur"),
    "bone": ("d2bf94", 0, .50, "horn"),
    "horn": ("50483f", 0, .38, "horn"),
    "red": ("983e39", 0, .63, "paint"),
    "purple": ("714661", 0, .64, "paint"),
    "blue": ("435d7e", 0, .66, "paint"),
    "white": ("d6cbb5", 0, .67, "paint"),
    "green": ("526849", 0, .65, "paint"),
    "teal": ("357575", 0, .63, "paint"),
    "sand": ("b79968", 0, .67, "paint"),
    "black": ("363b40", 0, .66, "paint"),
    "clay": ("ab6a4f", 0, .71, "ceramic"),
    "amber": ("cc812e", .04, .24, "stone"),
    "dark_resin": ("986131", 0, .43, "stone"),
    "resin": ("bc8d48", 0, .41, "stone"),
    "glass": ("4e8878", .13, .16, "stone"),
    "pearl": ("d8d1bc", .19, .22, "stone"),
    "parchment": ("d8bf91", 0, .83, "leather"),
    "fish": ("9b8a69", 0, .70, "horn"),
}
