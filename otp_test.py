import pyotp
import subprocess
from urllib.parse import urlparse, parse_qs

def run_parser(qrlink):

    command = [
        "python", "./otpauth-migration-decoder/src/decoder.py", "decode",
        "--migration", qrlink
    ]

    # Run the command and capture output
    result = subprocess.run(command, capture_output=True, text=True)

    # Get stdout and stderr
    output = result.stdout.strip()
    error = result.stderr.strip()

    # Print or use the output
    if result.returncode == 0:
        print("Decoder Output:\n", output)
    else:
        print("Error:\n", error)


    parsed = urlparse(output)
    query_params = parse_qs(parsed.query)

    secret = query_params.get("secret", [None])[0]
    print("Secret:", secret)

    totp = pyotp.TOTP(secret)
    return totp.now()