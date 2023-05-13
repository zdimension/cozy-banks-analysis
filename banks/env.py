# coding: utf-8
import dotenv

dotenv_file = dotenv.find_dotenv()
if not dotenv_file:
    # create empty .env file
    with open(".env", "w") as fp:
        fp.write("")
    dotenv_file = dotenv.find_dotenv()
    if not dotenv_file:
        print("Something is really wrong, .env not found after being created")
        exit(1)
dotenv.load_dotenv(dotenv_file)
