# Write your code here
#  MII 1 and 2 are issued by airlines
#  3 is issued by travel and entertainment
#  4 and 5 are issued by banking and financial institutions
#  6 is issued by merchandising and banking
#  7 is issued by petroleum companies
#  8 is issued by telecommunications companies
#  9 is issued by national assignment
#  First 6 digits should be 400000
#  16 digit numbers, after 400000 is a uuid with the last being the check
import random
import sys
import sqlite3


def getid():
    # This gets the last id # in the db and returns it + 1
    lastid = None
    con = sqlite3.connect('card.s3db', timeout=10)
    cu = con.cursor()
    for row in cu.execute('SELECT id FROM card;'):
        lastid = row[0]
    if lastid is None:
        # In the event there is no data in the table this will insure it starts at 0
        return 0
    return lastid + 1


def luhn(card):
    # The Luhn algorithm finds the check digit for a given sequence of numbers
    mtx = list()
    for i in card:
        mtx.append(int(i))
    # Adds all the digits to a list, card var is expected to be a str so it is iterable
    c = 0
    # This is expected to be used with 16 digit card numbers, with the last digit being removed prior to being passed
    while c < 15:
        if (c + 1) % 2 == 1:
            # multiply the odds by 2
            mtx[c] *= 2
        c += 1
    for i in mtx:
        if i > 9:
            # Subtract 9 from the digits over 9
            mtx[mtx.index(i)] -= 9
    if sum(mtx) % 10 != 0:
        # return the card string plus the check digit, calculated by the sum of all digits modulo 10, - 10
        return card + str(10 - (sum(mtx) % 10))
        # The reasoning for the - 10 is because if you modulo 57, for example, you need to get to the next 0 up
        # so it would be 3, however modulo 57 is 7, this you sub 10 to get 3
    else:
        # If it naturally lands on a 0
        return card + str((sum(mtx) % 10))


def create():
    # Establish a connection to the db, and a cursor to use it
    conn = sqlite3.connect('card.s3db', timeout=10)
    cur = conn.cursor()
    card = None
    pin = None
    # create a quasi-random uuid for the card. For info on why it is quasi-random
    # read the python documentation on the random module
    uuid = str(random.randint(0, 999999999))
    if len(uuid) != 9:
        uuid = "0" * (9 - len(uuid)) + uuid
        card = "400000" + uuid
    else:
        card = "400000" + uuid
    # Find the check digit
    card = luhn(card)
    # Create a pin
    pin = str(random.randint(0, 9999))
    if len(pin) != 4:
        # Fix the pin if it is not 4 digits
        pin = "0" * (4 - len(pin)) + pin
    lastid = getid()
    # Get the next id number for the new card, then insert the info into the db
    # I really should have made sure that the card was not already in the db, however
    # this is just a simple demo and I didn't want to spend more time on it.
    cur.execute('INSERT INTO card (id, number, pin, balance) VALUES (?, ?, ?, 0)', (lastid, card, pin))
    conn.commit()
    print(f"""Your card has been created
Your card number:
{card}
Your card PIN:
{pin}""")
    cur.close()
    return


def log(card):
    # Card number authenticated and logged in
    conn = sqlite3.connect('card.s3db', timeout=10)
    curs = conn.cursor()
    bal = 0
    print("You have successfully logged in!")
    # Fetch a list of all cards for easier comparison later
    # Not secure, but again, this is a simple demo
    cards = list()
    for rw in curs.execute('SELECT number FROM card;'):
        for thing in rw:
            if thing is not None:
                cards.append(thing)
    # Start the logged in loop
    while True:
        ch = input("""1. Balance
2. Add income
3. Do transfer
4. Close account
5. Log out
0. Exit
""")
        for row in curs.execute('SELECT balance FROM card WHERE number = ?;', [card]):
            bal = row[0]
        # Get the balance for the logged in card each time the loop starts so I don't have to do it later
        if ch == "1":
            # Self explanatory
            print(f"Balance: {bal}")
        elif ch == "2":
            # Also should be self explanatory
            income = input("Enter income:")
            bal = bal + int(income)
            curs.execute('UPDATE card SET balance = ? WHERE number = ?', (bal, card))
            conn.commit()
            print("Income was added!")
        elif ch == "3":
            # Transferring balance has quite a fwe error checks that makes it messy
            # Now that I'm going back over this commenting on it, you could probably transfer a negative amount
            print("Transfer")
            card2 = input("Enter card number:")
            # Get the card you're transferring to
            if card2 == luhn(card2[:-1]):
                # Check if the card passes the luhn algorithm
                if card2 in cards:
                    # Check if the card exists in the system
                    tran = int(input("Enter how much money you want to transfer:"))
                    # Get the amount you would like to transfer
                    if tran > bal:
                        # Check if you have enough funds to transfer
                        print("Not enough money!")
                    elif card == card2:
                        # See if you are trying to transfer to yourself
                        print("You cant transfer money to the same account!")
                    else:
                        # Subtract from your balance
                        curs.execute('UPDATE card SET balance = ? WHERE number = ?', (bal - tran, card))
                        conn.commit()
                        for row in curs.execute('SELECT balance FROM card WHERE number = ?;', [card2]):
                            bal2 = row[0]
                        # add to the other card's balance
                        curs.execute('UPDATE card SET balance = ? WHERE number = ?', (bal2 + tran, card2))
                        conn.commit()
                        print("Success!")
                else:
                    print("Such a card does not exist.")
            else:
                print("Probably you made a mistake in the card number. Please try again!")
        elif ch == "4":
            # Delete your account
            curs.execute('DELETE FROM card WHERE number = ? ', [card])
            conn.commit()
        elif ch == "5":
            print("You have successfully logged out!")
            break
        elif ch == "0":
            # Exit the program altogether
            print("Bye!")
            sys.exit(0)
        else:
            print("Wrong input, try again.")
    curs.close()


def auth():
    # Auth the card
    conn = sqlite3.connect('card.s3db', timeout=10)
    cur = conn.cursor()
    # Create a lit of all cards to use later
    accounts = list()
    for row in cur.execute('SELECT number FROM card;'):
        for thing in row:
            if thing is not None:
                accounts.append(thing)
    # Create a lit of all pins to use later
    # Both are ordered the same so the locations in the lists match with each other
    pins = list()
    for row in cur.execute('SELECT pin FROM card;'):
        for thing in row:
            if thing is not None:
                pins.append(thing)
    # init vars
    found = None
    loc = None
    # get login info
    ans1 = input("Enter your card number:")
    ans2 = input("Enter your PIN:")
    if ans1 in accounts:
        found = True
        # Card exists, get it's location in the list to compare to the pin
        loc = accounts.index(ans1)
    if found is not None:
        if pins[loc] == ans2:
            # Log in and pass the card # as an arg
            log(accounts[loc])
        else:
            print("Wrong card number or PIN!")
    else:
        print("Wrong card number or PIN!")
    cur.close()


# Establish a connection with the bd file, creating one if it does not exist.
# Additionally creating a cursor to execute commands
connn = sqlite3.connect('card.s3db', timeout=10)
curr = connn.cursor()
# If the db file exists, this does nothing
# if it does not this will create a table with appropriate parameters
try:
    curr.execute('SELECT * FROM card')
except sqlite3.OperationalError:
    curr.execute('CREATE TABLE card (id INTEGER, number TEXT, pin TEXT, balance INTEGER DEFAULT 0);')
curr.close()
# Start the main loop of the program for the text input
while True:
    ch = input("""1. Create an account
2. Log into account
0. Exit
""")
    if ch == "1":
        create()
    elif ch == "2":
        auth()
    elif ch == "0":
        print("Bye!")
        break
    else:
        print("Wrong input, try again.")
