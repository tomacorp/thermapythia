"""
Test Program for evaluating the PIL module, writing and reading PNG images
Tom Anderson
"""

from PIL import Image, ImageDraw
import time


filename= "pngtest.png"

imsize= 512
im = Image.new("RGB", (imsize, imsize), "black")

draw = ImageDraw.Draw(im)
draw.setfill("on")
draw.setink("yellow")
draw.line((0, im.size[1], im.size[0], 0), fill='blue', width=5)
draw.line((0, 0) + im.size, fill='green', width=10)

draw.rectangle((100,50,200,75))
draw.setink("red")
draw.ellipse((300,300,375,375))

del draw

# write to stdout
im.save(filename, 'PNG')
del im

#pix = im.load()
#print pix[x, y]
#pix[x, y] = value

imread= Image.open(filename, mode='r')
bands= imread.getbands()
print str(bands)
xysize= imread.size
width= xysize[0]
height= xysize[1]
print "Width: " + str(width) + " Height: " + str(height)

pix = imread.load()

hasred= 0
hasgreen= 0
hasblue= 0
for xn in range(0,imsize-1):
  for yn in range(0,imsize-1):
    if pix[xn,yn][0] > 0:
      hasred += 1
    if pix[xn,yn][1] > 0:
      hasgreen += 1
    if pix[xn,yn][2] > 0:
      hasblue += 1
print "Red count = " + str(hasred)
print "Green count = " + str(hasgreen)
print "Blue count = " + str(hasblue)
        
# 10Meg RGB Pixels uses 44MB, 16Meg RGB Pixels uses 75MB
#                  10 seconds,  17 seconds
# 1 Meg Pixel per second processing, 4.7 MB RAM per Meg Pixel
# .125 seconds or less to write and load 16Meg px simple image.
