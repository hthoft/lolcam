import time
from rpi_ws281x import *

# LED strip configuration:
LED_COUNT = 60        # Number of LED pixels.
LED_PIN = 23          # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10          # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

# Create NeoPixel object with appropriate configuration.
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
# Intialize the library (must be called once before other functions).
strip.begin()

def flash_strip(color, wait_ms=500):
    """Flash the LED strip with a given color and delay."""
    for _ in range(2):  # Flash twice
        # Turn on LEDs
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)
        
        # Turn off LEDs
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
        time.sleep(wait_ms / 1000.0)

# Main program logic follows:
if __name__ == '__main__':
    try:
        while True:
            print('Flashing LEDs')
            flash_strip(Color(255, 0, 0))  # Flash red
            time.sleep(1)  # Wait for a second before flashing again
    except KeyboardInterrupt:
        # Turn off all the LEDs on Ctrl+C
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
        print('LEDs turned off.')
