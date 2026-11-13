import os
from PIL import Image, ImageDraw, ImageFont

hub_dir = r"C:\Users\school57-60\.gemini\antigravity\scratch\Never_Hub\assets"
os.makedirs(hub_dir, exist_ok=True)

size = (256, 256)
img = Image.new("RGBA", size, (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Outer rounded dark cyber badge
# Background circle/rounded rect
draw.rounded_rectangle([8, 8, 247, 247], radius=54, fill=(13, 17, 28, 255), outline=(30, 41, 59, 255), width=4)

# Glowing outer ring
draw.ellipse([26, 26, 229, 229], outline=(56, 189, 248, 120), width=3)
draw.ellipse([32, 32, 223, 223], outline=(6, 182, 212, 180), width=4)

# Inner core background
draw.ellipse([42, 42, 213, 213], fill=(18, 24, 38, 255), outline=(244, 63, 94, 200), width=3)

# Glowing cyan accent dots
dots = [(128, 32), (223, 128), (128, 223), (32, 128)]
for x, y in dots:
    draw.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(56, 189, 248, 255))

# Draw futuristic geometric 'N'
# Points for 'N': left bar, diagonal, right bar
# Left bar: (82, 70) to (104, 186)
draw.polygon([(82, 72), (102, 72), (102, 184), (82, 184)], fill=(0, 240, 255, 255))
# Right bar: (152, 72) to (174, 184)
draw.polygon([(154, 72), (174, 72), (174, 184), (154, 184)], fill=(244, 63, 94, 255))
# Diagonal bar connecting top-left to bottom-right
draw.polygon([(92, 72), (114, 72), (174, 176), (152, 176)], fill=(236, 72, 153, 255))

# Small cyber dot above
draw.ellipse([122, 60, 134, 72], fill=(252, 238, 10, 255))

png_path = os.path.join(hub_dir, "never_hub.png")
ico_path = os.path.join(hub_dir, "never_hub.ico")

img.save(png_path, format="PNG")

# Save multi-size icon
sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
img.save(ico_path, format="ICO", sizes=sizes)
print("Saved icons successfully:", png_path, ico_path)
