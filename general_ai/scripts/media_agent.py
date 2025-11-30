"""
Media Intelligence Agent
------------------------
1. NEWS SCRAPER:
   - Action: Runs daily at 6:00 AM.
   - Sources: Trusted local/global sites.
   - Output: Bulleted summary email/briefing.

2. YOUTUBE WATCHER:
   - Tech: youtube-transcript-api
   - Workflow: Download Captions -> Gemini 1.5 Flash -> Summarize.
"""

from .youtube_watcher import YouTubeWatcher
from shared_utils import setup_logging

logger = setup_logging("MediaAgent")

class MediaAgent:
    def __init__(self):
        self.youtube = YouTubeWatcher()

    def get_news_briefing(self) -> dict:
        """
        Scrapes and summarizes top news stories.
        """
        # Placeholder for Beautiful Soup Logic
        return {
            "world": "Placeholder World News",
            "local": "Placeholder Local News",
            "weather": "Placeholder Weather"
        }

    def process_request(self, query: str) -> str:
        """
        Intelligent routing for media requests.
        Detects YouTube URLs and determines intent (Summarize vs Ask).
        """
        if "youtube.com" in query or "youtu.be" in query:
            # Extract URL
            words = query.split()
            url = next((w for w in words if "http" in w), None)
            
            if not url:
                return "I detected a YouTube request but couldn't find the link."

            if "summarize" in query.lower() or "summary" in query.lower() or "break down" in query.lower():
                logger.info(f"Processing YouTube Summary request for {url}")
                return self.youtube.summarize_video(url)
            
            else:
                # Treat as a specific question
                # Extract question part (simple heuristic: remove URL)
                question = query.replace(url, "").strip()
                if not question: 
                    question = "What is this video about?"
                
                logger.info(f"Processing YouTube Q&A for {url}")
                return self.youtube.ask_video(url, question)

        return "Media Agent: No recognizable media command found."