import os
import sys
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Load existing client ID and Secret from .env in parent directory
load_dotenv(dotenv_path="../.env")

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

if not client_id or not client_secret:
    print("Error: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in your .env file first!")
    sys.exit(1)

print("="*60)
print("Starting Spotify Authentication Process...")
print(f"Client ID: {client_id}")
print("="*60)
print("\nIMPORTANT: Make sure you have added the following Redirect URI in your")
print("Spotify Developer Dashboard app settings:")
print("👉 http://127.0.0.1:8888/callback")
print("\nIf you haven't added this redirect URI, Spotify will show an error page.")
print("="*60)

input("\nPress Enter to open your browser and authorize the application...")

scope = "user-modify-playback-state user-read-playback-state user-read-currently-playing"
redirect_uri = "http://127.0.0.1:8888/callback"

auth_manager = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    open_browser=True
)

try:
    # This will open a browser, wait for redirect, and retrieve the tokens
    token_info = auth_manager.get_access_token(as_dict=True)
    if token_info and 'refresh_token' in token_info:
        refresh_token = token_info['refresh_token']
        print("\n" + "="*60)
        print("🎉 SUCCESS! HERE IS YOUR SPOTIFY REFRESH TOKEN:")
        print("="*60)
        print(refresh_token)
        print("="*60)
        print("\nCopy the token above and add it to your .env file as:")
        print(f"SPOTIFY_REFRESH_TOKEN={refresh_token}")
        print("="*60)
    else:
        print("Error: Could not retrieve refresh token.")
except Exception as e:
    print(f"\nAuthorization failed: {e}")
    print("\nIf the browser opened but you got stuck, you can copy the URL you were redirected to")
    print("and paste it here if prompted, or retry the script.")
