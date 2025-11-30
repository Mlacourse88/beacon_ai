"""
YouTube Watcher Module
----------------------
Specialized tool for digesting video content.

Core Workflow:
1. 'Watch': Download closed captions/subtitles via `youtube_transcript_api`.
2. 'Think': Feed text to Gemini 1.5 Flash (Long Context) via GeneralAI.
3. 'Report': Output key takeaways.
"""

import logging
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# Import GeneralAI for summarization power
from general_ai.core_ai import GeneralAI
from shared_utils import setup_logging

logger = setup_logging("YouTubeWatcher")

class YouTubeWatcher:
    def __init__(self):
        # We need the GeneralAI to perform the summarization
        self.ai = GeneralAI()

    def _extract_video_id(self, url: str) -> str:
        """
        Parses video ID from various YouTube URL formats.
        """
        query = urlparse(url)
        if query.hostname == 'youtu.be':
            return query.path[1:]
        if query.hostname in ('www.youtube.com', 'youtube.com'):
            if query.path == '/watch':
                p = parse_qs(query.query)
                return p.get('v', [None])[0]
            if query.path[:7] == '/embed/':
                return query.path.split('/')[2]
            if query.path[:3] == '/v/':
                return query.path.split('/')[2]
        return ""

    def get_video_summary(self, video_url: str) -> str:
        """
        Fetches transcript and generates a summary.
        """
        video_id = self._extract_video_id(video_url)
        if not video_id:
            return "Error: Invalid YouTube URL."

        try:
            logger.info(f"Fetching transcript for video ID: {video_id}")
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            full_text = " ".join([t['text'] for t in transcript_list])
            
            prompt = f"""
            Summarize the following YouTube video transcript into 5 concise bullet points.
            Capture the main ideas and any specific action items.

            TRANSCRIPT:
            {full_text[:30000]} 
            """
            
            logger.info("Sending transcript to AI for summarization...")
            # Use sync invoke for simplicity in this context
            response = self.ai.llm.invoke(prompt)
            return response.content
            
        except (TranscriptsDisabled, NoTranscriptFound):
            return "Error: This video does not have closed captions/subtitles available."
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            return f"Error processing video: {e}"