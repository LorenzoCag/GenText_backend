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
    pause_duration = 0.5  # Add pause between messages

    if os.path.exists(text_audio_path):
        text_sound_clip = AudioFileClip(text_audio_path)
        text_sound_duration = text_sound_clip.duration

    final_frames = []
    frame_durations = []
    audio_clips = []
    current_time = 0

    # Calculate total frames needed for each message
    frames_per_message = len(transition_frames) // len(convo)
    
    for i, (voice_path, msg) in enumerate(zip(voice_audio_paths, convo)):
        # Add voice clip
        voice_clip = AudioFileClip(voice_path)
        voice_duration = voice_clip.duration
        voice_clip = voice_clip.set_start(current_time)
        audio_clips.append(voice_clip)

        # Add text sound if available
        if text_sound_clip is not None:
            text_sound = text_sound_clip.set_start(current_time)
            text_sound = text_sound.set_duration(min(text_sound_duration, voice_duration))
            text_sound = text_sound.volumex(0.5)
            audio_clips.append(text_sound)

        # Calculate frames needed for this message
        message_frames = int((voice_duration + pause_duration) * 24)  # 24 fps
        start_frame = i * frames_per_message
        
        # Add frames for the message duration
        for frame in range(message_frames):
            progress = min(1.0, frame / message_frames)
            frame_index = start_frame + int(progress * frames_per_message)
            frame_index = min(frame_index, len(transition_frames) - 1)
            
            final_frames.append(transition_frames[frame_index])
            frame_durations.append(1/24)
        
        current_time += voice_duration + pause_duration

    # Create the final video clip
    video_clip = ImageSequenceClip(final_frames, durations=frame_durations)
    video_clip = video_clip.set_audio(CompositeAudioClip(audio_clips))

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
    pause_duration = 0.5  # Add pause between messages

    if os.path.exists(text_audio_path):
        text_sound_clip = AudioFileClip(text_audio_path)
        text_sound_duration = text_sound_clip.duration

    final_frames = []
    frame_durations = []
    audio_clips = []
    current_time = 0

    # Calculate total frames needed for each message
    frames_per_message = len(transition_frames) // len(convo)
    
    for i, (voice_path, msg) in enumerate(zip(voice_audio_paths, convo)):
        # Add voice clip
        voice_clip = AudioFileClip(voice_path)
        voice_duration = voice_clip.duration
        voice_clip = voice_clip.set_start(current_time)
        audio_clips.append(voice_clip)

        # Add text sound if available
        if text_sound_clip is not None:
            text_sound = text_sound_clip.set_start(current_time)
            text_sound = text_sound.set_duration(min(text_sound_duration, voice_duration))
            text_sound = text_sound.volumex(0.5)
            audio_clips.append(text_sound)

        # Calculate frames needed for this message
        message_frames = int((voice_duration + pause_duration) * 24)  # 24 fps
        start_frame = i * frames_per_message
        
        # Add frames for the message duration
        for frame in range(message_frames):
            progress = min(1.0, frame / message_frames)
            frame_index = start_frame + int(progress * frames_per_message)
            frame_index = min(frame_index, len(transition_frames) - 1)
            
            final_frames.append(transition_frames[frame_index])
            frame_durations.append(1/24)
        
        current_time += voice_duration + pause_duration

    # Create the final video clip
    video_clip = ImageSequenceClip(final_frames, durations=frame_durations)
    video_clip = video_clip.set_audio(CompositeAudioClip(audio_clips))

    output_filename = f"chat_video_{job_id}.mp4" if job_id else "chat_video_scroll.mp4"
    output_path = os.path.join(output_dir, output_filename)
    video_clip.write_videofile(output_path, fps=24, audio_codec="aac")

    return output_path


if __name__ == "__main__":
    output_path = generate_video("A conversation about coding", "great rizz", 15)
    print(f"Video generated: {output_path}")
