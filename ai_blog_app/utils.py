import os
import assemblyai as aai
import openai
from django.conf import settings
from pytube import YouTube
from django.contrib.auth.models import User
from .models import BlogPost

def youtube_title(link):
    youtube = YouTube(link)
    title = youtube.title
    return title

def download_audio(link):
    youtube = YouTube(link)
    video_audio = youtube.streams.filter(only_audio=True).first()
    out_file = video_audio.download(output_path=settings.MEDIA_ROOT)
    base, ext = os.path.splitext(out_file)
    new_file = base + '.mp3'
    os.rename(out_file, new_file)
    return new_file

def get_transcription(link):
    audio_file = download_audio(link)
    aai.settings.api_key = os.getenv('AAI_API_KEY')

    try:
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_file)
        transcription_text = transcript.text
    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        transcription_text = None
    finally:
        # Remove the audio file after processing
        if os.path.exists(audio_file):
            os.remove(audio_file)
            print(f"Deleted audio file: {audio_file}")

    return transcription_text

def generate_blog_from_transcription(transcription):
    openai.api_key = os.getenv('OPENAI_API_KEY')

    prompt = f"Based on the following transcript from a YouTube video, \
        write a comprehensive blog article, write it based on the transcript, \
            but dont make it look like a youtube video, \
                make it look like a proper blog article:\n\n{transcription}\n\nArticle:"
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Replace with a suitable model from OpenAI's current options
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": ""},
            ],
            max_tokens=1000,
            timeout=30  # Example: set timeout to 30 seconds
        )
        generated_content = response['choices'][0]['message']['content'].strip()
        return generated_content
    except openai.error.APIError as e:
        print(f"OpenAI API Error: {e.message}")
        return None
    except Exception as e:
        print(f"Error generating blog content: {str(e)}")
        return None

def process_youtube_video(user_id, youtube_link):
    user = User.objects.get(id=user_id)
    
    # Get title
    title = youtube_title(youtube_link)

    # Get transcript
    transcription = get_transcription(youtube_link)
    if not transcription:
        return None, 'Failed to get transcript 😭'

    # Use OpenAI to generate the blog
    blog_content = generate_blog_from_transcription(transcription)
    if not blog_content:
        return None, 'Failed to generate blog article 😭'

    # Save blog article into database
    new_blog_article = BlogPost.objects.create(
        user=user,
        youtube_title=title,
        youtube_link=youtube_link,
        generated_content=blog_content,
    )
    new_blog_article.save()

    return new_blog_article, None
