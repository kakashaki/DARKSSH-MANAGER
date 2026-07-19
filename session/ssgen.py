import os
from time import sleep

a = r"""
 
┏━━━┳━━━┳━━━┳┓┏━┳━━━┳━━━┳┓╋┏┓
┗┓┏┓┃┏━┓┃┏━┓┃┃┃┏┫┏━┓┃┏━┓┃┃╋┃┃
╋┃┃┃┃┃╋┃┃┗━┛┃┗┛┛┃┗━━┫┗━━┫┗━┛┃
╋┃┃┃┃┗━┛┃┏┓┏┫┏┓┃┗━━┓┣━━┓┃┏━┓┃
┏┛┗┛┃┏━┓┃┃┃┗┫┃┃┗┫┗━┛┃┗━┛┃┃╋┃┃
┗━━━┻┛╋┗┻┛┗━┻┛┗━┻━━━┻━━━┻┛╋┗┛
"""


def spinner():
    print("Checking if Telethon is installed...")
    for _ in range(3):
        for frame in r"-\|/-\|/":
            print("\b", frame, sep="", end="", flush=True)
            sleep(0.1)


def clear_screen():
    # https://www.tutorialspoint.com/how-to-clear-screen-in-python#:~:text=In%20Python%20sometimes%20we%20have,screen%20by%20pressing%20Control%20%2B%20l%20.
    if os.name == "posix":
        os.system("clear")
    else:
        # for windows platfrom
        os.system("cls")


def get_api_id_and_hash():
    print(
        "Get your API ID and API HASH from my.telegram.org or @ScrapperRoBot to proceed.\n\n",
    )
    try:
        API_ID = int(input("Please enter your API ID: "))
    except ValueError:
        print("APP ID must be an integer.\nQuitting...")
        exit(1)
    API_HASH = input("Please enter your API HASH: ")
    return API_ID, API_HASH


def telethon_session():
    spinner()
    try:
        import telethon  # noqa: F401

        x = "\bFound an existing installation of Telethon...\nSuccessfully Imported.\n\n"
    except ImportError:
        print("Installing Telethon...")
        if os.system("pip install -U telethon") != 0:
            print("Failed to install Telethon. Please install it manually.\nQuitting...")
            exit(1)
        try:
            import telethon  # noqa: F401
        except ImportError as e:
            print(f"Telethon is still not importable after install: {e}\nQuitting...")
            exit(1)
        x = "\bDone. Installed and imported Telethon."
    clear_screen()
    print(a)
    print(x)

    # the imports

    from telethon.errors.rpcerrorlist import ApiIdInvalidError, PhoneNumberInvalidError
    from telethon.sessions import StringSession
    from telethon.sync import TelegramClient

    API_ID, API_HASH = get_api_id_and_hash()

    # logging in
    try:
        with TelegramClient(StringSession(), API_ID, API_HASH) as ultroid:
            print("Generating a user session for DARKSSH...")
            ult = ultroid.send_message(
                "me",
                f"**DARKSSH** `SESSION`:\n\n`{ultroid.session.save()}`\n\n**Do not share this anywhere!**",
            )
            print(
                "Your SESSION has been generated. Check your telegram saved messages!"
            )
            exit(0)
    except ApiIdInvalidError:
        print(
            "Your API ID/API HASH combination is invalid. Kindly recheck.\nQuitting..."
        )
        exit(1)
    except ValueError:
        print("API HASH must not be empty!\nQuitting...")
        exit(1)
    except PhoneNumberInvalidError:
        print("The phone number is invalid!\nQuitting...")
        exit(1)


def main():
    clear_screen()
    print(a)
    telethon_session()
    x = input("Run again? (y/n")
    if x == "y":
        main()
    else:
        exit(0)


main()
