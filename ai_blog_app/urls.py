from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('signup', views.user_signup, name='signup'),
    path('login', views.user_login, name='login'),
    path('logout', views.user_logout, name='logout'),
    path('generate-blog', views.generate_blog, name='generate-blog'),
    path('blog-posts', views.blog_posts, name='blog-posts'),
    path('blog-details/<int:pk>', views.blog_details, name='blog-details'),
]
