from pyicloud import PyiCloudService
import os
import sys

def check_for_2fa(api):
    if api.requires_2fa:
        print("Two-factor authentication required.")
        code = input("Enter the code you received of one of your approved devices: ")
        result = api.validate_2fa_code(code)
        print("Code validation result: %s" % result)

        if not result:
            print("Failed to verify security code")
            sys.exit(1)

        if not api.is_trusted_session:
            print("Session is not trusted. Requesting trust...")
            result = api.trust_session()
            print("Session trust result %s" % result)

            if not result:
                print("Failed to request trust. You will likely be prompted for the code again in the coming weeks")
    elif api.requires_2sa:
        import click
        print("Two-step authentication required. Your trusted devices are:")

        devices = api.trusted_devices
        for i, device in enumerate(devices):
            print("  %s: %s" % (i, device.get('deviceName',
                "SMS to %s" % device.get('phoneNumber'))))

        device = click.prompt('Which device would you like to use?', default=0)
        device = devices[device]
        if not api.send_verification_code(device):
            print("Failed to send verification code")
            sys.exit(1)

        code = click.prompt('Please enter validation code')
        if not api.validate_verification_code(device, code):
            print("Failed to verify verification code")
            sys.exit(1)

def get_files(item, path):
    if item.type == 'file':
        yield (item, path)
        return
    for name in item.dir():
        yield from get_files(item[name], f'{path}/{name}')


def main():
    path = sys.argv[1]
    root = path.rpartition('/')[0]
    user = sys.argv[2]
    password = sys.argv[3]
    api = PyiCloudService(user, password)
    check_for_2fa(api)
    item = api.drive
    for f in path.split('/'):
        item = item[f]
    for file, path in get_files(item, path):
        loc = os.path.relpath(path, root)
        dir = os.path.dirname(loc)
        os.makedirs(dir, exist_ok=True)
        if os.path.exists(loc):
            print(f'Path {loc} already exists, skipping')
            continue
        download = file.open(stream=True)
        print('Downloading', loc)
        with open(loc, 'wb') as f:
            f.write(download.raw.read())


if __name__ == '__main__':
    main()