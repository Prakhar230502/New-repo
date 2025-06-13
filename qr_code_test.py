from PIL import Image
from pyzbar.pyzbar import decode

# Load the QR code image
image = Image.open("pqu.jpg")

# Decode QR code
decoded_objects = decode(image)

for obj in decoded_objects:
    data = obj.data.decode("utf-8")
    print("Decoded QR URL:", data)
