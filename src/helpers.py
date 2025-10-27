def cents_to_dollars_str(value):
    """Default printing function. Input value in cents"""
    amount = value
    if amount < 0:
        amount = amount * -1
    dollars = int(amount / 100)
    cents = amount % 100

    if cents < 10:
        cents = "0" + str(cents)
    else:
        cents = str(cents)

    dollar_output = ""

    while dollars > 0:
        dollar_temp = dollars % 1000
        dollars = int(dollars / 1000)

        if dollars > 0:
            if dollar_temp < 10:
                dollar_temp = "00" + str(dollar_temp)
            elif dollar_temp < 100:
                dollar_temp = "0" + str(dollar_temp)

        dollar_output = str(dollar_temp) + dollar_output

        if dollars > 0:
            dollar_output = "," + dollar_output

    return (
        ("-" if value < 0 else "")
        + "$"
        + (dollar_output if len(dollar_output) > 0 else "0")
        + "."
        + cents
    )
