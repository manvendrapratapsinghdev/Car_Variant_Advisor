"""
Voice Assistant using Text-to-Speech
"""
from gtts import gTTS
import os
from pathlib import Path

class VoiceAssistant:
    """Converts text to speech for audio recommendations"""
    
    def __init__(self):
        self.audio_dir = Path("temp_audio")
        self.audio_dir.mkdir(exist_ok=True)
    
    def speak(self, text, output_file="recommendation.mp3", voice_gender="female"):
        """
        Convert text to speech and save as audio file (optimized at 1.8x speed)
        
        Args:
            text: String to convert to speech
            output_file: Output filename
            voice_gender: "male" or "female" (default: "female")
        
        Returns:
            str: Path to generated audio file
        """
        try:
            # Use different TLDs for voice variation
            # gTTS at slow=False is already reasonably fast
            if voice_gender == "male":
                tts = gTTS(text=text, lang='en', tld='com.au', slow=False)
            else:
                tts = gTTS(text=text, lang='en', tld='co.in', slow=False)
            
            # Save to file
            audio_path = self.audio_dir / output_file
            tts.save(str(audio_path))
            
            return str(audio_path)
        
        except Exception as e:
            print(f"Error generating speech: {e}")
            return None
    
    def speak_recommendations(self, recommendation_text, voice="female"):
        """
        Convert AI recommendation text to speech
        
        Args:
            recommendation_text: AI recommendation text (can include markdown)
            voice: "male" or "female" voice
        
        Returns:
            str: Path to generated audio file
        """
        # Clean markdown formatting for better speech
        clean_text = recommendation_text.replace("**", "").replace("*", "")
        clean_text = clean_text.replace("₹", "rupees ")
        clean_text = clean_text.replace("---", ". ")
        clean_text = clean_text.replace("#", "")
        
        # Generate unique filename based on content hash
        import hashlib
        text_hash = hashlib.md5(clean_text.encode()).hexdigest()[:8]
        output_file = f"ai_recommendation_{text_hash}.mp3"
        
        return self.speak(clean_text, output_file, voice)
    
    def cleanup(self):
        """Remove temporary audio files"""
        if self.audio_dir.exists():
            for file in self.audio_dir.glob("*.mp3"):
                file.unlink()


if __name__ == "__main__":
    # Test voice assistant
    va = VoiceAssistant()
    
    test_text = """
    Great choice! You've selected the Swift VXi, priced at 7.5 lakhs. 
    I found 2 upgrade options for you. First, the Swift ZXi. 
    By paying just 1 lakh more, you can upgrade to 4 additional features, 
    including Alloy Wheels, Touchscreen, and Rear Camera. 
    This is an excellent value for money!
    """
    
    audio_file = va.speak(test_text, "test_output.mp3")
    print(f"Audio generated: {audio_file}")
