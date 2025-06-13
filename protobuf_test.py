from otpauth_migration_decoder import decode

url = "otpauth-migration://offline?data=CkIKFFClacKd3jvJYQNgYtqdUQnlp24qEgZVWjQ4MjAaB1plcm9kaGEgASgBMAJCEzI0M2RiZjE3NDc4OTA0MDgzNzgQAhgBIAA%3D"
otp_entries = decode(url)

for entry in otp_entries:
    print("Issuer:", entry.issuer)
    print("Account Name:", entry.name)
    print("Secret:", entry.secret)
    print("OTP URL:", entry.url)
