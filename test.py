from PIL import Image

filepath = 'map.png'

im=Image.open(filepath)
print(im.size) 