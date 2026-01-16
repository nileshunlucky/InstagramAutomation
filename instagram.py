
import os
import random
import time
import logging
import requests
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Instagram Graph API credentials
IG_USER_ID = os.getenv("IG_USER_ID")
ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")

# Instagram captions
CAPTIONS = [
    "Comment 'M' to get FREE access to AI 😮‍💨. #youtube #thumbnail #graphic #ai #photoshop",
    "Comment 'M' to make viral thumbnails 😏. #graphic #photoshop #youtube #ai #thumbnail",
    "Comment 'M' to get this tool for FREE 🤩. #youtube #thumbnail #photoshop #ai #graphic",
]


def fetch_random_video_from_cloudinary():
    """Fetch a random video from the specified Cloudinary folder."""
    try:
        videos = [
                "https://res.cloudinary.com/dccsatiwa/video/upload/v1768581894/VID_20260116_084117_146_bsl_jxgpgz.mp4",
                "https://res.cloudinary.com/dccsatiwa/video/upload/v1768581894/VID_20260116_080743_608_bsl_kw81vy.mp4",
                "https://res.cloudinary.com/dccsatiwa/video/upload/v1768581889/VID_20260116_081202_364_bsl_qachh1.mp4",
                "https://res.cloudinary.com/dccsatiwa/video/upload/v1768581888/VID_20260116_083445_695_bsl_ljgfa2.mp4",
                "https://res.cloudinary.com/dccsatiwa/video/upload/v1768581888/VID_20260116_080909_939_bsl_ojqdsu.mp4",
                "https://res.cloudinary.com/dccsatiwa/video/upload/v1768581888/VID_20260116_081059_472_bsl_qjzbut.mp4",
                "https://res.cloudinary.com/dccsatiwa/video/upload/v1768581887/VID_20260116_080611_069_bsl_qgkwqn.mp4",
        ]

        video = random.choice(videos)
        video_url = video.get("secure_url")
        
        if not video_url or not video_url.startswith("https://"):
            logger.error(f"Invalid video URL: {video_url}")
            return None
            
        return video_url
    except Exception as e:
        logger.error(f"Error fetching video from Cloudinary: {str(e)}")
        return None


def wait_for_video_processing(creation_id, max_attempts=10, delay=5):
    """Wait for Instagram to finish processing the video."""
    for attempt in range(max_attempts):
        try:
            status_res = requests.get(
                f"https://graph.facebook.com/v19.0/{creation_id}",
                params={"fields": "status_code", "access_token": ACCESS_TOKEN}
            )
            status_data = status_res.json()
            
            if "error" in status_data:
                logger.error(f"Error checking status: {status_data['error']}")
                return False
                
            status = status_data.get("status_code")
            logger.info(f"Video status: {status} (attempt {attempt+1}/{max_attempts})")
            
            if status == "FINISHED":
                return True
            if status in ["ERROR", "REJECTED"]:
                logger.error(f"Video processing failed with status: {status}")
                return False
                
            time.sleep(delay)
        except Exception as e:
            logger.error(f"Error checking video status: {str(e)}")
            time.sleep(delay)
    
    logger.error("Video processing timed out")
    return False


def post_video_to_instagram(video_url, caption):
    """Post a video to Instagram using the Graph API."""
    if not IG_USER_ID or not ACCESS_TOKEN:
        logger.error("Missing Instagram credentials. Check environment variables.")
        return False

    logger.info("Starting Instagram video upload process...")

    try:
        # Step 1: Create container for the video
        create_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media"
        create_payload = {
            "video_url": video_url,
            "caption": caption,
            "media_type": "REELS",
            "access_token": ACCESS_TOKEN
        }

        create_res = requests.post(create_url, data=create_payload)
        create_data = create_res.json()

        if "id" not in create_data:
            logger.error(f"Failed to create media container: {create_data}")
            return False

        creation_id = create_data["id"]
        logger.info(f"Media container created with ID: {creation_id}")

        # Step 2: Wait for video processing
        if not wait_for_video_processing(creation_id):
            return False

        # Step 3: Publish the processed video
        publish_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish"
        publish_payload = {
            "creation_id": creation_id,
            "access_token": ACCESS_TOKEN
        }

        publish_res = requests.post(publish_url, data=publish_payload)
        publish_data = publish_res.json()

        if "id" in publish_data:
            post_id = publish_data["id"]
            logger.info(f"Video published successfully! Post ID: {post_id}")
        else:
            logger.error(f"Failed to publish video: {publish_data}")
            return False
            
    except Exception as e:
        logger.error(f"Error during Instagram posting: {str(e)}")
        return False


def post_random_video():
    """Main function to post a random video with a random caption."""
    logger.info(f"Running Instagram post task at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get a random video
    video_url = fetch_random_video_from_cloudinary()
    if not video_url:
        return False
    
    # Get a random caption
    caption = random.choice(CAPTIONS)
    
    # Post to Instagram
    success = post_video_to_instagram(video_url, caption)
    
    if success:
        logger.info(f"Successfully posted video to Instagram: {video_url}")
        return True
    else:
        logger.error("Failed to post video to Instagram")
        return False
