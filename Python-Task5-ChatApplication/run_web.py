"""Start the web chat:  python3 run_web.py   then open http://127.0.0.1:5001"""

from web_chat.app import create_app

# Port 5001, not 5000: on recent macOS versions AirPlay Receiver uses port 5000.
HOST = "127.0.0.1"
PORT = 5001

app, socketio = create_app()

if __name__ == "__main__":
    print(f"Web chat running at http://{HOST}:{PORT}  (press Ctrl+C to stop)")
    # allow_unsafe_werkzeug: Flask's development server is fine for a local demo.
    socketio.run(app, host=HOST, port=PORT, allow_unsafe_werkzeug=True)
