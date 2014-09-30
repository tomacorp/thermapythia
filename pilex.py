"""
Test Program for evaluating the PIL module, writing and reading PNG images
Tom Anderson
"""

from PIL import Image, ImageDraw

filename= "pngtest.png"

im = Image.new("RGB", (512, 512), "white")

draw = ImageDraw.Draw(im)
draw.setfill("on")
draw.setink("black")
draw.line((0, 0) + im.size, fill=128)
draw.line((0, im.size[1], im.size[0], 0), fill=128)

draw.rectangle((100,50,200,75))
draw.setink("red")
draw.ellipse((300,300,375,375))

del draw

# write to stdout
im.save(filename, 'PNG')
del im

imread= Image.open(filename, mode='r')
bands= imread.getbands()
print str(bands)
px= imread.getpixel((110, 60))
print str(px)
px= imread.getpixel((25, 25))
print str(px)
px= imread.getpixel((335, 335))
print str(px)

