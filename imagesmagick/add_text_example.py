from wand.image import Image
from wand.drawing import Drawing

ny = Image(filename ='black.jpg')
draw = Drawing()
draw.font_size = 20
draw.text(100, 100, 'Hello world!!')
draw(ny)
ny.save(filename= 'text.jpg')
