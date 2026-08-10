import os
import time
import requests

URL = "https://download.pytorch.org/whl/cu124/torch-2.6.0%2Bcu124-cp311-cp311-win_amd64.whl"
FILENAME = "torch-2.6.0+cu124-cp311-cp311-win_amd64.whl"
CHUNK_SIZE = 1024 * 1024  # 1 MB

def download_with_resume(url, filename):
    print(f"Starting resilient download of {filename}")
    headers = {}
    mode = 'wb'
    downloaded = 0
    
    if os.path.exists(filename):
        downloaded = os.path.getsize(filename)
        print(f"File exists. Resuming from {downloaded / (1024*1024):.1f} MB...")
        headers['Range'] = f'bytes={downloaded}-'
        mode = 'ab'

    try:
        response_head = requests.head(url, allow_redirects=True, timeout=10)
        total_size = int(response_head.headers.get('content-length', 0))
        if total_size > 0:
            print(f"Total file size: {total_size / (1024*1024*1024):.2f} GB")
        
        if downloaded >= total_size and total_size > 0:
            print("File is already fully downloaded.")
            return True
            
    except Exception as e:
        print(f"Could not get total file size initially: {e}")
        total_size = 0

    retries = 0
    while True:
        try:
            if downloaded > 0:
                headers['Range'] = f'bytes={downloaded}-'
            else:
                headers.pop('Range', None)
                
            print(f"\nConnecting to server... (attempt {retries + 1})")
            with requests.get(url, headers=headers, stream=True, timeout=15) as r:
                r.raise_for_status()
                
                # If server doesn't support Range, it returns 200 instead of 206
                if r.status_code == 200 and downloaded > 0:
                    print("Warning: Server didn't honor Range header, restarting download...")
                    downloaded = 0
                    mode = 'wb'
                    
                with open(filename, mode) as f:
                    for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if downloaded % (50 * 1024 * 1024) < CHUNK_SIZE: # Print every ~50 MB
                                if total_size > 0:
                                    print(f"Downloaded: {downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB")
                                else:
                                    print(f"Downloaded: {downloaded / (1024*1024):.1f} MB")
            
            print(f"\nDownload complete! Total size: {downloaded / (1024*1024):.1f} MB")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
            retries += 1
            print("Waiting 3 seconds before retrying...")
            time.sleep(3)
            mode = 'ab'  # Switch to append mode for next retry

if __name__ == "__main__":
    success = download_with_resume(URL, FILENAME)
    if success:
        print("\n--- Download Success! Beginning Installation ---")
        
        # Install the local wheel file
        print("\nInstalling PyTorch...")
        os.system(f".\\venv\\Scripts\\python.exe -m pip install {FILENAME} torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124")
        
        # Install other requirements
        print("\nInstalling remaining NLP dependencies...")
        os.system(".\\venv\\Scripts\\python.exe -m pip install transformers peft bitsandbytes accelerate evaluate scikit-learn datasets pandas matplotlib seaborn")
        
        print("\n--- ALL INSTALLATIONS COMPLETE ---")
