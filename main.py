from gen_messages import generate_fake_convo
from draw_image import draw_convo_scroll_frames
from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeAudioClip
from audio import generate_voice_clips
from gen_profile import generate_contact_image
from PIL import Image
from io import BytesIO
import base64
import os
from PIL import Image


def generate_video(prompt, style, n_messages, job_id=None):
    convo = generate_fake_convo(n_messages=n_messages, style=style, prompt=prompt)

    base_dir = os.path.dirname(__file__)
    output_dir = os.path.join(base_dir, "output")
    frame_dir = os.path.join(output_dir, "frames")
    os.makedirs(frame_dir, exist_ok=True)

    transition_frames = draw_convo_scroll_frames(
        convo,
        contact_name="Alice",
        profile_image_path="Profile.jpg",
        output_dir=frame_dir,
        num_transition_frames=5
    )

    # Generate frames with reveal animation
    base_frames, transition_frames, message_bottom_positions, base_frames_dir, transitions_dir = draw_convo_scroll_frames(
        convo,
        contact_name="Alice",
        profile_image_path="Profile.jpg"
    )

    voice_audio_paths = generate_voice_clips(convo, user_voice="nova", other_voice="fable")
    text_audio_path = os.path.join(base_dir, "text_audio.mp4")
    text_sound_clip = None
    text_sound_duration = 0.5  # Default duration for text sound effect

    if os.path.exists(text_audio_path):
        text_sound_clip = AudioFileClip(text_audio_path)
        text_sound_duration = text_sound_clip.duration

    audio_paths = []
    for voice in voice_audio_paths:
        if text_sound_clip is not None:
            audio_paths.append(text_audio_path)
        audio_paths.append(voice)

    final_frames = []
    frame_durations = []
    audio_clips = []

    frame_index = 0
    current_frame = transition_frames[0]

    # Create video clips with synchronized audio
    video_clips = []
    fps = 30  # Frames per second for smooth reveal
    reveal_duration = 1.0  # Duration of reveal in seconds
    frames_per_reveal = int(fps * reveal_duration)

    # Group frames by message
    message_frames = {}
    for frame_path in base_frames:
        # Extract message index from filename (frameX_msgY_ZZZ.png or frameX_msgY_final.png)
        parts = os.path.basename(frame_path).split('_')
        if len(parts) >= 2 and parts[1].startswith('msg'):
            msg_idx = int(parts[1][3:])
            if msg_idx not in message_frames:
                message_frames[msg_idx] = []
            message_frames[msg_idx].append(frame_path)

    # Sort message indices
    msg_indices = sorted(message_frames.keys())

    # Create video clips for each message with its audio
    for i, msg_idx in enumerate(msg_indices):
        # Get frames for this message
        msg_frames = message_frames[msg_idx]

        # Create audio clip and get its duration
        audio_clip = AudioFileClip(audio_paths[msg_idx])
        duration = audio_clip.duration
        start_time = sum(frame_durations)

        audio_clips.append(audio_clip.set_start(start_time))

        hold_frames = int(duration * 24)
        for _ in range(hold_frames):
            safe_index = min(frame_index, len(transition_frames) - 1)
            final_frames.append(transition_frames[safe_index])
            frame_durations.append(1 / 24)

        if is_voice_clip and frame_index + 5 <= len(transition_frames) - 1:
            for _ in range(5):
                frame_index += 1
                safe_index = min(frame_index, len(transition_frames) - 1)
                final_frames.append(transition_frames[safe_index])
                frame_durations.append(1 / 24)

        # Create video clip for the reveal animation
        reveal_frames = [f for f in msg_frames if not f.endswith('_final.png')]
        reveal_clip = ImageSequenceClip(reveal_frames, fps=fps).set_duration(reveal_duration)

        # Create a clip that holds the final frame for the remaining duration
        final_frames = [f for f in msg_frames if f.endswith('_final.png')]
        if final_frames:
            final_frame = final_frames[0]
            hold_clip = ImageSequenceClip([final_frame], fps=1).set_duration(duration - reveal_duration)

            # Combine reveal and hold clips
            msg_clip = concatenate_videoclips([reveal_clip, hold_clip])
        else:
            # If no final frame, just use the reveal clip
            msg_clip = reveal_clip

        # Add the text sound effect at the beginning of each message if available
        if text_sound_clip is not None:
            # Create a composite audio with both the message audio and text sound
            text_sound = text_sound_clip.set_start(0).set_duration(min(text_sound_duration, duration)).volumex(0.5)
            composite_audio = CompositeAudioClip([audio_clip, text_sound])
            msg_clip = msg_clip.set_audio(composite_audio)
        else:
            # If no text sound, just use the message audio
            msg_clip = msg_clip.set_audio(audio_clip)

        video_clips.append(msg_clip)

    # Concatenate all clips
    final_clip = concatenate_videoclips(video_clips)

    # Generate output filename
    if job_id:
        output_filename = f"chat_video_{job_id}.mp4"
    else:
        output_filename = "chat_video_scroll.mp4"

    output_filename = f"chat_video_{job_id}.mp4" if job_id else "chat_video_scroll.mp4"
    output_path = os.path.join(output_dir, output_filename)
    video_clip.write_videofile(output_path, fps=24, audio_codec="aac")

    return output_path

    try:
        # Write video file
        final_clip.write_videofile(output_path, fps=24, audio_codec="aac")
        print(f"Video generated successfully: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error generating video: {e}")
        return None


def generate_video_from_json(data, job_id=None):
    contact_name = data["contact_name"]
    contact_gender = data["contact_gender"].lower()
    your_gender = data["your_gender"].lower()
    convo = data["convo"]

    voice_map = {
        "male": "ash",
        "female": "sage"
    }

    user_voice = voice_map.get(your_gender, "nova")
    other_voice = voice_map.get(contact_gender, "fable")

    base_dir = os.path.dirname(__file__)
    output_dir = os.path.join(base_dir, "output")
    frame_dir = os.path.join(output_dir, "frames")
    os.makedirs(frame_dir, exist_ok=True)

    # Always generate initials-based profile image
    print(f"[INFO] Generating initials-based profile image for '{contact_name}'...")
    profile_picture_path = os.path.join(output_dir, f"profile_{contact_name.replace(' ', '_')}_initials.png")
    img = generate_contact_image(contact_name)
    img.save(profile_picture_path)

    # Render message frames
    transition_frames = draw_convo_scroll_frames(
        convo,
        contact_name=contact_name,
        profile_image_path=profile_picture_path,
        output_dir=frame_dir,
        num_transition_frames=5
    )

    # Generate voice and timing
    voice_audio_paths = generate_voice_clips(convo, user_voice=user_voice, other_voice=other_voice)
    text_audio_path = os.path.join(base_dir, "text_audio.mp4")
    text_sound_clip = None
    text_sound_duration = 0.5  # Default duration for text sound effect

    if os.path.exists(text_audio_path):
        text_sound_clip = AudioFileClip(text_audio_path)
        text_sound_duration = text_sound_clip.duration

    audio_paths = []
    for voice in voice_audio_paths:
        if text_sound_clip is not None:
            audio_paths.append(text_audio_path)
        audio_paths.append(voice)

    final_frames = []
    frame_durations = []
    audio_clips = []

    frame_index = 0

    for i, audio_path in enumerate(audio_paths):
        is_voice_clip = (i % 2 == 1)
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        start_time = sum(frame_durations)

        audio_clips.append(audio_clip.set_start(start_time))

        hold_frames = int(duration * 24)
        for _ in range(hold_frames):
            safe_index = min(frame_index, len(transition_frames) - 1)
            final_frames.append(transition_frames[safe_index])
            frame_durations.append(1 / 24)

        if is_voice_clip and frame_index + 5 <= len(transition_frames) - 1:
            for _ in range(5):
                frame_index += 1
                safe_index = min(frame_index, len(transition_frames) - 1)
                final_frames.append(transition_frames[safe_index])
                frame_durations.append(1 / 24)

    video_clip = ImageSequenceClip(final_frames, durations=frame_durations)
    video_clip = video_clip.set_audio(CompositeAudioClip(audio_clips))

    output_filename = f"chat_video_{job_id}.mp4" if job_id else "chat_video_scroll.mp4"
    output_path = os.path.join(output_dir, output_filename)
    video_clip.write_videofile(output_path, fps=24, audio_codec="aac")

    return output_path


if __name__ == "__main__":
    output_path = generate_video("A conversation about coding", "great rizz", 15)
    print(f"Video generated: {output_path}")
