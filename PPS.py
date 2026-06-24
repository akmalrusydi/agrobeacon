from gpiozero import Button
from signal import pause

pps = Button(21)

def pulse():

    print("PPS DETECTED")

pps.when_pressed = pulse

print("Waiting PPS...")

pause()