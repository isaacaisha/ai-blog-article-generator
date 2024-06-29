from celery import shared_task
from .utils import process_youtube_video

@shared_task
def async_process_youtube_video(user_id, youtube_link):
    new_blog_article, error_message = process_youtube_video(user_id, youtube_link)
    if error_message:
        return {'error': error_message}
    return {'content': new_blog_article.generated_content}
