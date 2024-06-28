import json
import os
import assemblyai as aai
import openai
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings

from pytube import YouTube
from .models import BlogPost


# Create your views here.
@login_required
def index(request):
    return render(request, 'index.html')


@csrf_exempt
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            youtube_link = data['link']
        except(KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid data sent 😭'}, status=400)
        
        # get title
        title = youtube_title(youtube_link)

        # get transcript
        transcription = get_transcription(youtube_link)
        if not transcription:
            return JsonResponse({'error': 'Failed to get transcript 😭'}, status=500)

        # use openai to generate the blog
        blog_content =  generate_blog_from_transcription(transcription)
        if not blog_content:
            return JsonResponse({'error': 'Failed to generate blog article 😭'}, status=500)

        # save blog article into database
        new_blog_article = BlogPost.objects.create(
            user=request.user,
            youtube_title=title,
            youtube_link=youtube_link,
            generated_content=blog_content,
            #created_at=,
        )
        new_blog_article.save()

        # return blog article as a response
        return JsonResponse({'content': blog_content})

    else:
        return JsonResponse({'error': 'Invalid request method 🤣'}, status=405)
    

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

    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)
    return transcript.text


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


def user_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirmPassword = request.POST['confirmPassword']

        if password == confirmPassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except:
                error_message = 'Something went Wrong, creating the account 😭'
                return render(request, 'signup.html', {'error_message': error_message})
        else:
            error_message = 'Password doesn\'t match 😝'
            return render(request, 'signup.html', {'error_message': error_message})
    return render(request, 'signup.html')


def user_login(request):
    if request.method =='POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error_message = 'Invalid username or password 🤪'
            return render(request, 'login.html', {'error_message': error_message})
    return render(request, 'login.html')


def user_logout(request):
    logout(request)
    return redirect('/')


def blog_posts(request):
    blog_articles = BlogPost.objects.filter(user=request.user) 
    return render(request, 'blog-posts.html', {'blog_articles': blog_articles})


def blog_details(request, pk):
    blog_article_detail = BlogPost.objects.get(id=pk)
    if request.user == blog_article_detail.user:
        return render(request, 'blog-details.html', 
                      {'blog_article_detail': blog_article_detail})
    else:
        return redirect('/')
