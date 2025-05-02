import time 
  

import random
from flask import Flask
app = Flask(__name__)

def countdown(t): 
    while t: 
        mins, secs = divmod(t, 60) 
        timer = '{:02d}:{:02d}'.format(mins, secs) 
        print(timer, end="\r") 
        time.sleep(1) 
        t -= 1
        
  
countdown(int(60)) 

@app.route("/")
def test_timer():
    
    return "No hablo queso!"


if __name__ == "__main__":  # true if this file NOT imported
    app.debug = True        # enable auto-reload upon code change
    app.run()
#function for counting down time
# connect to html and show fountdown on screen real time
#functinality for when start button clicked
