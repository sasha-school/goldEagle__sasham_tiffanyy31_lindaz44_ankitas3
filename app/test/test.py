import time 
  

import random
from flask import Flask
app = Flask(__name__)

  


@app.route("/")
def test_timer():
    
   
    return render_template("dashboard.html", ticks = t)


if __name__ == "__main__":  # true if this file NOT imported
    app.debug = True        # enable auto-reload upon code change
    app.run()
#function for counting down time
# connect to html and show fountdown on screen real time
#functinality for when start button clicked
