from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import subprocess
import threading
import queue
import time

# Global request queue
request_queue = queue.Queue()

# Repeat controller
repeat_event = threading.Event()
repeat_thread = None

def speak_text(text):
    """Run Piper for text and then play via aplay."""
    safe_text = text.replace('"', '\\"')
    cmd_piper = [
        "python3", "-m", "piper",
        "-m", "en_GB-southern_english_female-low",
        "-f", "test.wav",
        "--", safe_text
    ]
    subprocess.run(cmd_piper, check=True)
    subprocess.Popen(["aplay", "test.wav"])

def play_file(filename):
    """Play an existing WAV file."""
    subprocess.Popen(["aplay", filename])

def repeat_worker(text):
    """Background worker to repeat text every 2s until stopped."""
    while not repeat_event.wait(2):  # wait 2s, exit if event is set
        try:
            speak_text(text)
        except Exception as e:
            print(f"Repeat worker error: {e}")
            break

class TTSHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global repeat_thread

        query = parse_qs(urlparse(self.path).query)
        text_list = query.get("text", [])

        if not text_list:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Error: No 'text' parameter provided.\n")
            return

        text = text_list[0]

        # Any new request stops current repeating
        if repeat_thread and repeat_thread.is_alive():
            repeat_event.set()
            repeat_thread.join()
            repeat_thread = None
            repeat_event.clear()

        try:
            if text.startswith(">"):
                filename = text[1:].strip()
                if filename:
                    play_file(filename)
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(f"Playing file: {filename}\n".encode())
                else:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Error: No filename after '>'\n")

            elif text.startswith(":"):
                spoken_text = text[1:].strip()
                if spoken_text:
                    # Speak once immediately
                    speak_text(spoken_text)
                    # Start repeating thread
                    repeat_thread = threading.Thread(
                        target=repeat_worker, args=(spoken_text,), daemon=True
                    )
                    repeat_thread.start()
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(f"Repeating speech started: {spoken_text}\n".encode())
                else:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Error: No text after ':'\n")

            else:
                # Normal speech (once only)
                speak_text(text)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(f"Text processed and spoken: {text}\n".encode())

        except subprocess.CalledProcessError as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error running command: {e}\n".encode())


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 4601), TTSHandler)
    print("Server running on port 4601...")
    server.serve_forever()

