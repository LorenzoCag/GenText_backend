from PIL import Image, ImageDraw, ImageFont, ImageOps
import textwrap
import os
import platform
import math


# Handle deprecation of ANTIALIAS
try:
    RESAMPLING = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLING = Image.LANCZOS
WIDTH = 375
FRAME_HEIGHT = 667
HEADER_HEIGHT = 120  # taller to fit profile image + name
PADDING = 20
BUBBLE_PADDING = 10
FONT_SIZE = 18
PROFILE_IMG_SIZE = 50

# Dark mode colors
BACKGROUND_COLOR = "#121212"  # Dark background
HEADER_BG_COLOR = "#1E1E1E"   # Slightly lighter dark for header
USER_BUBBLE_COLOR = "#0A84FF" # iOS blue for user messages
OTHER_BUBBLE_COLOR = "#2C2C2E" # Dark gray for other messages
USER_TEXT_COLOR = "#FFFFFF"   # White text for user messages
OTHER_TEXT_COLOR = "#FFFFFF"  # White text for other messages
HEADER_TEXT_COLOR = "#FFFFFF" # White text for header

# Use system fonts based on OS
if platform.system() == "Darwin":  # macOS
    FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"  # Helvetica is guaranteed to exist on macOS
elif platform.system() == "Windows":
    FONT_PATH = "C:\\Windows\\Fonts\\arial.ttf"
else:  # Linux and others
    FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Verify font exists
if not os.path.exists(FONT_PATH):
    # Fallback fonts for macOS
    fallback_fonts = [
        "/System/Library/Fonts/SFNSText.ttf",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/Library/Fonts/Arial.ttf"
    ]

    for font in fallback_fonts:
        if os.path.exists(font):
            FONT_PATH = font
            break
    else:
        raise FileNotFoundError(f"Could not find any suitable font. Please install a TrueType font.")

def get_text_width(font, text):
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]

def get_text_height(lines):
    return len(lines) * (FONT_SIZE + 5) + BUBBLE_PADDING

def draw_ios_bubble_with_curve(draw, x0, y0, x1, y1, fill, is_user=False):
    """Draw an iOS-style bubble with a smooth curve from the edge to a point outside."""
    # Basic bubble parameters
    corner_radius = 20

    # Draw the main rounded rectangle
    draw.rounded_rectangle([x0, y0, x1, y1], radius=20, fill=fill)


def render_messages_to_frame(messages, font, contact_name="Contact", profile_image_path=None):
    total_height = HEADER_HEIGHT + PADDING
    message_boxes = []

    for msg in messages:
        lines = textwrap.wrap(msg["text"], width=30)
        height = get_text_height(lines) + 10  # spacing
        message_boxes.append((msg, lines, height))
        total_height += height

    # Create image with dark background
    img = Image.new("RGB", (WIDTH, FRAME_HEIGHT), color=BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)

    # Header background with dark mode color
    draw.rectangle([0, 0, WIDTH, HEADER_HEIGHT], fill=HEADER_BG_COLOR)

    # Draw profile picture (centered circle)
    if profile_image_path and os.path.exists(profile_image_path):
        profile_img = Image.open(profile_image_path).convert("RGB")
        profile_img = profile_img.resize((PROFILE_IMG_SIZE, PROFILE_IMG_SIZE), RESAMPLING)

        # Create circular mask
        mask = Image.new("L", (PROFILE_IMG_SIZE, PROFILE_IMG_SIZE), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, PROFILE_IMG_SIZE, PROFILE_IMG_SIZE), fill=255)

        # Apply mask and paste centered
        profile_img = ImageOps.fit(profile_img, (PROFILE_IMG_SIZE, PROFILE_IMG_SIZE), centering=(0.5, 0.5))
        img.paste(profile_img, ((WIDTH - PROFILE_IMG_SIZE) // 2, 10), mask)

    # Draw contact name below the image with dark mode text color
    header_font = ImageFont.truetype(FONT_PATH, 20)
    text_width = get_text_width(header_font, contact_name)
    draw.text(((WIDTH - text_width) / 2, 10 + PROFILE_IMG_SIZE + 5), contact_name, font=header_font, fill=HEADER_TEXT_COLOR)

    # Draw messages starting below header
    y = HEADER_HEIGHT + PADDING
    for msg, lines, _ in message_boxes:
        is_user = msg["sender"] == "You"
        bubble_color = USER_BUBBLE_COLOR if is_user else OTHER_BUBBLE_COLOR
        text_color = USER_TEXT_COLOR if is_user else OTHER_TEXT_COLOR

        bubble_width = max([get_text_width(font, line) for line in lines]) + 2 * BUBBLE_PADDING
        bubble_height = get_text_height(lines)

        x0 = WIDTH - bubble_width - PADDING if is_user else PADDING
        y0 = y
        x1 = x0 + bubble_width
        y1 = y0 + bubble_height

        # Use the iOS bubble with curve function
        draw_ios_bubble_with_curve(draw, x0, y0, x1, y1, bubble_color, is_user)

        text_y = y0 + BUBBLE_PADDING // 2
        for line in lines:
            draw.text((x0 + BUBBLE_PADDING, text_y), line, font=font, fill=text_color)
            text_y += FONT_SIZE + 5

        y = y1 + 10

    return img

def draw_convo_scroll_frames(convo, contact_name="Contact", profile_image_path=None, output_dir=None, num_transition_frames=5):
    if output_dir is None:
        base_dir = os.path.dirname(__file__)
        output_dir = os.path.join(base_dir, "output", "frames")

    os.makedirs(output_dir, exist_ok=True)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    frames = []
    visible_msgs = []
    cumulative_height = HEADER_HEIGHT + PADDING

    for i, msg in enumerate(convo):
        lines = textwrap.wrap(msg["text"], width=30)
        msg_height = get_text_height(lines) + 10
        new_height = cumulative_height + msg_height

        # If adding the next message exceeds the screen, reset to top
        if new_height > FRAME_HEIGHT:
            visible_msgs = []
            cumulative_height = HEADER_HEIGHT + PADDING

        visible_msgs.append(msg)
        cumulative_height += msg_height

        # Calculate where the new message will appear (slide from below)
        y_position = HEADER_HEIGHT + PADDING
        for m in visible_msgs[:-1]:
            y_position += get_text_height(textwrap.wrap(m["text"], width=30)) + 10

        for j in range(1, num_transition_frames + 1):
            temp_img = Image.new("RGB", (WIDTH, FRAME_HEIGHT), color=BACKGROUND_COLOR)
            draw = ImageDraw.Draw(temp_img)

            # Draw header
            draw.rectangle([0, 0, WIDTH, HEADER_HEIGHT], fill=HEADER_BG_COLOR)
            if profile_image_path and os.path.exists(profile_image_path):
                profile_img = Image.open(profile_image_path).convert("RGB")
                profile_img = profile_img.resize((PROFILE_IMG_SIZE, PROFILE_IMG_SIZE), RESAMPLING)
                mask = Image.new("L", (PROFILE_IMG_SIZE, PROFILE_IMG_SIZE), 0)
                draw_mask = ImageDraw.Draw(mask)
                draw_mask.ellipse((0, 0, PROFILE_IMG_SIZE, PROFILE_IMG_SIZE), fill=255)
                profile_img = ImageOps.fit(profile_img, (PROFILE_IMG_SIZE, PROFILE_IMG_SIZE), centering=(0.5, 0.5))
                temp_img.paste(profile_img, ((WIDTH - PROFILE_IMG_SIZE) // 2, 10), mask)

            header_font = ImageFont.truetype(FONT_PATH, 20)
            text_width = get_text_width(header_font, contact_name)
            draw.text(((WIDTH - text_width) / 2, 10 + PROFILE_IMG_SIZE + 5), contact_name, font=header_font, fill=HEADER_TEXT_COLOR)

            # Draw old messages
            y = HEADER_HEIGHT + PADDING
            for m in visible_msgs[:-1]:
                lines = textwrap.wrap(m["text"], width=30)
                is_user = m["sender"] == "You"
                bubble_color = USER_BUBBLE_COLOR if is_user else OTHER_BUBBLE_COLOR
                text_color = USER_TEXT_COLOR if is_user else OTHER_TEXT_COLOR
                bubble_width = max([get_text_width(font, line) for line in lines]) + 2 * BUBBLE_PADDING
                bubble_height = get_text_height(lines)
                x0 = WIDTH - bubble_width - PADDING if is_user else PADDING
                x1 = x0 + bubble_width
                y1 = y + bubble_height
                draw_ios_bubble_with_curve(draw, x0, y, x1, y1, bubble_color, is_user)
                text_y = y + BUBBLE_PADDING // 2
                for line in lines:
                    draw.text((x0 + BUBBLE_PADDING, text_y), line, font=font, fill=text_color)
                    text_y += FONT_SIZE + 5
                y += bubble_height + 10

            # Slide-in new message
            slide_progress = j / num_transition_frames
            slide_y_offset = int((1 - slide_progress) * 50)
            lines = textwrap.wrap(msg["text"], width=30)
            is_user = msg["sender"] == "You"
            bubble_color = USER_BUBBLE_COLOR if is_user else OTHER_BUBBLE_COLOR
            text_color = USER_TEXT_COLOR if is_user else OTHER_TEXT_COLOR
            bubble_width = max([get_text_width(font, line) for line in lines]) + 2 * BUBBLE_PADDING
            bubble_height = get_text_height(lines)
            x0 = WIDTH - bubble_width - PADDING if is_user else PADDING
            x1 = x0 + bubble_width
            y0 = y_position + slide_y_offset
            y1 = y0 + bubble_height
            draw_ios_bubble_with_curve(draw, x0, y0, x1, y1, bubble_color, is_user)
            text_y = y0 + BUBBLE_PADDING // 2
            for line in lines:
                draw.text((x0 + BUBBLE_PADDING, text_y), line, font=font, fill=text_color)
                text_y += FONT_SIZE + 5

            frame_path = os.path.join(output_dir, f"frame_{len(frames):03}.png")
            temp_img.save(frame_path)
            frames.append(frame_path)

    return frames
