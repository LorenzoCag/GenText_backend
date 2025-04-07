from PIL import Image, ImageDraw, ImageFont
import os
import platform

def generate_contact_image(name, size=256, font_size=100, font_path=None):
    # Extract initials
    initials = "".join([part[0] for part in name.split()[:2]]).upper()

    # Create square image
    img = Image.new("RGB", (size, size))
    draw = ImageDraw.Draw(img)

    # Draw gradient background (darker)
    for y in range(size):
        gradient = int(50 + 55 * (y / size))  # dark gray to slightly lighter gray
        draw.line([(0, y), (size, y)], fill=(gradient, gradient, gradient))

    # Load font
    if not font_path:
        if platform.system() == "Darwin":
            font_path = "/System/Library/Fonts/SFNSDisplay.ttf"
        elif platform.system() == "Windows":
            font_path = "C:\\Windows\\Fonts\\arial.ttf"
        else:
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    if not os.path.exists(font_path):
        raise FileNotFoundError("Font not found at: " + font_path)

    font = ImageFont.truetype(font_path, font_size)

    # Calculate text position to center it
    bbox = font.getbbox(initials)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2 - 10

    # Draw initials
    draw.text((text_x, text_y), initials, font=font, fill=(255, 255, 255))

    # Make it circular
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, size, size), fill=150)
    img.putalpha(mask)

    return img
