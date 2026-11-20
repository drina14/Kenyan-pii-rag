import phonenumbers

numbers = ["0722 456 789", "0110 234 567", "0745 789 012", "0701 678 901", "0701 678 901"]
for n, region in zip(numbers, ["GB", "GB", "GB", "GB", "KE"]):
    try:
        p = phonenumbers.parse(n, region)
        print(f"{n!r:16} region={region}  valid={phonenumbers.is_valid_number(p)}")
    except Exception as e:
        print(f"{n!r:16} region={region}  error: {e}")