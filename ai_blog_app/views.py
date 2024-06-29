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

from .tasks import process_youtube_video
from .utils import youtube_title, download_audio,get_transcription, generate_blog_from_transcription, process_youtube_video


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
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid data sent 😭'}, status=400)

        new_blog_article, error_message = process_youtube_video(request.user.id, youtube_link)

        if error_message:
            return JsonResponse({'error': error_message}, status=500)
        
        return JsonResponse({'content': new_blog_article.generated_content})

    return JsonResponse({'error': 'Invalid request method 🤣'}, status=405)


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
