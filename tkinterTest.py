#!/Users/toma/python278i/bin/python
# Tom Anderson


from Tkinter import *
root = Tk()
# All of this would do better as a subclass of Canvas with specialize methods
def drawcircle(canv,x,y,rad):
# changed this to return the ID
    return canv.create_oval(x-rad,y-rad,x+rad,y+rad,width=0,fill='blue')

def movecircle(canv, cir):
    canv.move(cir,-1,-1)
    
# Elliptic arcs cannot rotate.
def movearc(canv, a):
    canv.move(a,1,1)
    
def drawEllipticArc(canv,x,y,rad):
    return canv.create_arc([x-2*rad,y-rad,x+2*rad,y+rad],start=-30, extent= 105, width=0,fill='green')
    
def callback(event):
    movecircle(canvas, circ1)
    movecircle(canvas, circ2)
    movearc(canvas, arc)

canvas = Canvas(width=600, height=200, bg='white')
canvas.bind("<Button-1>", callback)
canvas.pack(expand=YES, fill=BOTH)
text = canvas.create_text(50,10, text="Tk test")
arc = drawEllipticArc(canvas, 200, 100, 10)
circ1=drawcircle(canvas,100,100,20)          
circ2=drawcircle(canvas,500,100,20)
root.mainloop()