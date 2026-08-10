import os
import time
import urllib.request

def notify(topic):
    try:
        req = urllib.request.Request(
            f"https://ntfy.sh/{topic}", 
            data=b"Your AI Agent needs terminal approval to restart the script! Please check your laptop.", 
            method="POST"
        )
        req.add_header("Title", "AI Agent Alert")
        req.add_header("Priority", "urgent")
        urllib.request.urlopen(req)
    except Exception as e:
        print("Failed to send notification:", e)

def main():
    topic = "vaibhav_indic_agent_8821" # Unique topic
    print(f"============================================================")
    print(f"📱 PHONE NOTIFIER ACTIVE")
    print(f"============================================================")
    print(f"To receive alerts on your phone:")
    print(f"1. Download the 'ntfy' app (free, no account needed)")
    print(f"2. Subscribe to the topic: vaibhav_indic_agent_8821")
    print(f"   (Or just leave https://ntfy.sh/vaibhav_indic_agent_8821 open in your phone browser)")
    print(f"============================================================")
    print(f"Listening for approval requests...")
    
    trigger_file = "trigger_notification.txt"
    while True:
        if os.path.exists(trigger_file):
            try:
                os.remove(trigger_file)
                notify(topic)
                print(f"[{time.strftime('%H:%M:%S')}] 🔔 Sent push notification to phone!")
            except Exception as e:
                pass
        time.sleep(3)

if __name__ == "__main__":
    main()
