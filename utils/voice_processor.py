import os
import tempfile
import requests
import whisper
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceProcessor:
    def __init__(self):
        """Initialize the voice processor with Whisper model"""
        try:
            # Load Whisper model (will download on first use)
            logger.info("Loading Whisper model...")
            self.model = whisper.load_model("base")
            logger.info("✅ Whisper model loaded successfully!")
        except Exception as e:
            logger.error(f"❌ Error loading Whisper model: {str(e)}")
            self.model = None
    
    def download_voice_file(self, file_id: str, telegram_token: str) -> Optional[str]:
        """
        Download voice file from Telegram
        
        Args:
            file_id: Telegram file ID
            telegram_token: Telegram bot token
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            # Get file info from Telegram
            file_info_url = f"https://api.telegram.org/bot{telegram_token}/getFile"
            file_info_response = requests.get(file_info_url, params={"file_id": file_id})
            
            if file_info_response.status_code != 200:
                logger.error(f"❌ Failed to get file info: {file_info_response.text}")
                return None
            
            file_info = file_info_response.json()
            if not file_info.get("ok"):
                logger.error(f"❌ File info not ok: {file_info}")
                return None
            
            file_path = file_info["result"]["file_path"]
            
            # Download the file
            download_url = f"https://api.telegram.org/file/bot{telegram_token}/{file_path}"
            download_response = requests.get(download_url)
            
            if download_response.status_code != 200:
                logger.error(f"❌ Failed to download file: {download_response.status_code}")
                return None
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg")
            temp_file.write(download_response.content)
            temp_file.close()
            
            logger.info(f"✅ Voice file downloaded: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"❌ Error downloading voice file: {str(e)}")
            return None
    
    def transcribe_voice(self, file_path: str) -> Dict[str, Any]:
        """
        Transcribe voice file to text using Whisper
        
        Args:
            file_path: Path to the voice file
            
        Returns:
            Dictionary with transcription result
        """
        try:
            if not self.model:
                return {
                    "success": False,
                    "error": "Whisper model not loaded",
                    "transcript": ""
                }
            
            logger.info(f"🎤 Transcribing voice file: {file_path}")
            
            # Transcribe the audio
            result = self.model.transcribe(file_path)
            
            transcript = result["text"].strip()
            
            if transcript:
                logger.info(f"✅ Transcription successful: '{transcript}'")
                return {
                    "success": True,
                    "transcript": transcript,
                    "language": result.get("language", "unknown"),
                    "confidence": result.get("confidence", 0.0)
                }
            else:
                logger.warning("⚠️ Transcription returned empty text")
                return {
                    "success": False,
                    "error": "No speech detected",
                    "transcript": ""
                }
                
        except Exception as e:
            logger.error(f"❌ Error transcribing voice: {str(e)}")
            return {
                "success": False,
                "error": f"Transcription error: {str(e)}",
                "transcript": ""
            }
    
    def process_voice_message(self, file_id: str, telegram_token: str) -> Dict[str, Any]:
        """
        Complete voice processing pipeline
        
        Args:
            file_id: Telegram file ID
            telegram_token: Telegram bot token
            
        Returns:
            Dictionary with processing result
        """
        downloaded_file = None
        
        try:
            # Step 1: Download voice file
            downloaded_file = self.download_voice_file(file_id, telegram_token)
            if not downloaded_file:
                return {
                    "success": False,
                    "error": "Failed to download voice file",
                    "transcript": ""
                }
            
            # Step 2: Transcribe voice
            transcription_result = self.transcribe_voice(downloaded_file)
            
            return transcription_result
            
        except Exception as e:
            logger.error(f"❌ Error in voice processing pipeline: {str(e)}")
            return {
                "success": False,
                "error": f"Voice processing error: {str(e)}",
                "transcript": ""
            }
        
        finally:
            # Step 3: Clean up - delete downloaded file
            if downloaded_file and os.path.exists(downloaded_file):
                try:
                    os.unlink(downloaded_file)
                    logger.info(f"🗑️ Deleted voice file: {downloaded_file}")
                except Exception as e:
                    logger.error(f"❌ Error deleting voice file: {str(e)}")

# Global instance
voice_processor = VoiceProcessor()

def process_voice_message(file_id: str, telegram_token: str) -> Dict[str, Any]:
    """
    Convenience function to process voice messages
    
    Args:
        file_id: Telegram file ID
        telegram_token: Telegram bot token
        
    Returns:
        Dictionary with transcription result
    """
    return voice_processor.process_voice_message(file_id, telegram_token) 