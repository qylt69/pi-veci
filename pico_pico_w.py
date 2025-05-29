# MicroPython: Simple onboard LED blink with web control for Pico W
import network
import socket
import time
from machine import Pin, ADC
import _thread
import sys
import ubinascii
import uhashlib

# CONFIGURE THESE
# SSID and PASSWORD are no longer stored in code for security.
COUNTRY = 'SK'

# Prompt for Wi-Fi credentials securely at boot
try:
    ssid = input('Enter Wi-Fi SSID: ')
    password = input('Enter Wi-Fi password: ')
except Exception as e:
    print('Error reading Wi-Fi credentials:', e)
    sys.exit()

led = Pin('LED', Pin.OUT)
led_on = False
blink_delay = 1.0

# Wi-Fi utilities for robust scanning and connection
def scan_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print('Scanning for all Wi-Fi networks (detailed)...')
    try:
        nets = wlan.scan()
    except Exception as e:
        print('Wi-Fi scan failed:', e)
        return []
    results = []
    if nets:
        print(f'Found {len(nets)} networks:')
        for net in nets:
            try:
                ssid = net[0].decode() if isinstance(net[0], bytes) else str(net[0])
            except:
                ssid = str(net[0])
            bssid = ':'.join('{:02x}'.format(b) for b in net[1])
            channel = net[2]
            rssi = net[3]
            authmode = net[4]
            hidden = net[5]
            auth_desc = {
                0: 'OPEN',
                1: 'WEP',
                2: 'WPA-PSK',
                3: 'WPA2-PSK',
                4: 'WPA/WPA2-PSK',
                5: 'WPA2-ENTERPRISE',
            }.get(authmode, str(authmode))
            print(f'  SSID: "{ssid}" | BSSID: {bssid} | Channel: {channel} | RSSI: {rssi} | Auth: {auth_desc} | Hidden: {hidden}')
            results.append({
                'ssid': ssid,
                'bssid': bssid,
                'channel': channel,
                'rssi': rssi,
                'authmode': authmode,
                'auth_desc': auth_desc,
                'hidden': hidden
            })
    else:
        print('No Wi-Fi networks found!')
    return results

def connect_wifi(ssid=None, password=None, country='SK', max_attempts=20):
    if not ssid or not password:
        print('ERROR: Real SSID and password must be provided at runtime.')
        return False
    wlan = network.WLAN(network.STA_IF)
    network.country(country)
    wlan.active(True)
    print(f'Connecting to Wi-Fi SSID: {ssid}...')
    wlan.connect(ssid, password)
    for i in range(max_attempts):
        status = wlan.status()
        print(f'  Attempt {i+1}/{max_attempts}... status: {status}')
        if wlan.isconnected():
            print('Connected:', wlan.ifconfig()[0])
            return True
        time.sleep(1)
    print('Wi-Fi failed!')
    return False

# Onboard temperature sensor (ADC4)
def read_onboard_temp():
    sensor = ADC(4)
    reading = sensor.read_u16() * 3.3 / 65535
    temp_c = 27 - (reading - 0.706) / 0.001721
    return temp_c

# LED blinker thread
def led_blinker():
    global led_on, blink_delay
    last_state = None
    last_delay = None
    last_temp = None
    last_temp_time = 0
    while True:
        temp = read_onboard_temp()
        now = time.time()
        if last_temp is None or now - last_temp_time > 60:
            print(f'Temperature: {temp:.2f}°C')
            last_temp = temp
            last_temp_time = now
        if led_on:
            led.value(1)
            if last_state != led_on or last_delay != blink_delay:
                print(f'LED ON (delay={blink_delay}s)')
            time.sleep(blink_delay)
            led.value(0)
            if last_state != led_on or last_delay != blink_delay:
                print(f'LED OFF (delay={blink_delay}s)')
            time.sleep(blink_delay)
        else:
            led.value(0)
            if last_state != led_on:
                print('LED OFF (forced)')
            time.sleep(0.1)
        last_state = led_on
        last_delay = blink_delay

# Morse code dictionary
MORSE_CODE_DICT = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
    ' ': '/',
}

def text_to_morse(text):
    return ' '.join(MORSE_CODE_DICT.get(c.upper(), '') for c in text)

def blink_morse(message):
    global led
    DOT = 0.2
    DASH = 0.6
    GAP = 0.2
    LETTER_GAP = 0.6
    WORD_GAP = 1.4
    morse = text_to_morse(message)
    print(f'Morse for "{message}": {morse}')
    print('update terminal')
    for symbol in morse:
        if symbol == '.':
            led.value(1)
            time.sleep(DOT)
            led.value(0)
            time.sleep(GAP)
        elif symbol == '-':
            led.value(1)
            time.sleep(DASH)
            led.value(0)
            time.sleep(GAP)
        elif symbol == ' ':
            time.sleep(LETTER_GAP)
        elif symbol == '/':
            time.sleep(WORD_GAP)
    print('Morse code done')

# Web server
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Pico W LED</title>
<style>
body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #232946; color: #eebbc3; margin: 0; padding: 0; }}
.container {{ max-width: 400px; margin: 40px auto; background: #121629; border-radius: 16px; box-shadow: 0 4px 24px #0008; padding: 32px; }}
h2 {{ color: #fffffe; margin-top: 0; }}
label {{ font-weight: bold; }}
input, select {{ border-radius: 6px; border: 1px solid #b8c1ec; padding: 6px; margin: 6px 0 12px 0; width: 100%; background: #232946; color: #fffffe; }}
input[type=submit] {{ background: #eebbc3; color: #232946; font-weight: bold; border: none; cursor: pointer; transition: background 0.2s; }}
input[type=submit]:hover {{ background: #fffffe; color: #232946; }}
p {{ margin: 10px 0; }}
.status {{ background: #b8c1ec; color: #232946; border-radius: 8px; padding: 10px; margin-top: 18px; font-size: 1.1em; }}
.temp {{ font-size: 1.2em; color: #fffffe; }}
</style>
</head>
<body>
<div class="container">
<h2>Pico W LED & Temperature Control</h2>
<form>
  <label>LED State:</label>
  <select name="led">
    <option value="on" {on_sel}>ON</option>
    <option value="off" {off_sel}>OFF</option>
  </select><br>
  <label>Blink Delay (s):</label>
  <input type="number" step="0.1" name="delay" value="{delay}"><br>
  <input type="submit" value="Update">
  <label>Morse Name:</label> <input type="text" name="morse" placeholder="Type name"> <input type="submit" value="Send Morse">
  <input type="submit" name="stop" value="Stop Pico" formmethod="get">
</form>
<div class="status">
  <p>Current: <b>{state}</b>, Delay: <b>{delay}</b>s</p>
  <p class="temp">Onboard Temperature: <b>{temp:.2f}°C</b></p>
</div>
</div>
</body>
</html>
"""

def web_server():
    global led_on, blink_delay
    ports = [80, 8080, 8081]
    s = None
    wlan = network.WLAN(network.STA_IF)
    ip = wlan.ifconfig()[0] if wlan.isconnected() else '<not connected>'
    for port in ports:
        addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]
        s = socket.socket()
        try:
            s.bind(addr)
            print(f'Web server running! Visit: http://{ip}:{port}')
            break
        except OSError as e:
            if e.errno == 98:
                print(f'Port {port} in use, trying next...')
                s.close()
                s = None
                continue
            else:
                raise
    if s is None:
        print('Error: All tested ports are in use. Please reset the Pico or wait and try again.')
        return
    s.listen(1)
    while True:
        cl, _ = s.accept()
        req = cl.recv(1024).decode()
        changed = False
        # Parse GET
        if 'GET /?' in req:
            params = req.split(' ')[1].split('?',1)[1].split(' ')[0]
            morse_name = None
            for p in params.split('&'):
                if p.startswith('led='):
                    new_led_on = (p.split('=')[1] == 'on')
                    if new_led_on != led_on:
                        led_on = new_led_on
                        changed = True
                if p.startswith('delay='):
                    try:
                        new_delay = max(0.1, float(p.split('=')[1]))
                        if new_delay != blink_delay:
                            blink_delay = new_delay
                            changed = True
                    except:
                        pass
                if p.startswith('morse='):
                    morse_name = p.split('=')[1].replace('+', ' ')
                if p.startswith('stop=1'):
                    print('Stopping Pico program by web request.')
                    cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
                    cl.send('<html><body><h2>Pico stopped.</h2></body></html>')
                    cl.close()
                    sys.exit()
            if morse_name:
                blink_morse(morse_name)
        on_sel = 'selected' if led_on else ''
        off_sel = '' if led_on else 'selected'
        temp = read_onboard_temp()
        html = HTML.format(
            on_sel=on_sel, off_sel=off_sel,
            delay=blink_delay, state='ON' if led_on else 'OFF', temp=temp)
        cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        cl.send(html)
        cl.close()
        if changed:
            print(f'Web update: LED {"ON" if led_on else "OFF"}, delay={blink_delay}s')

# --- Secure password input ---
def prompt_for_wifi():
    global SSID, PASSWORD
    if not SSID:
        SSID = input('Enter Wi-Fi SSID: ')
    if not PASSWORD:
        try:
            # Try to hide password input (works in some MicroPython builds)
            import getpass
            PASSWORD = getpass.getpass('Enter Wi-Fi password: ')
        except:
            PASSWORD = input('Enter Wi-Fi password: ')

# Main
networks = scan_wifi()
if connect_wifi(ssid, password, COUNTRY):
    _thread.start_new_thread(led_blinker,())
    web_server()
else:
    print('Could not connect to Wi-Fi.')