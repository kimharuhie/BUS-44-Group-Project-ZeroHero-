#This function is used to find if a string is present in a list (i.e. find a username)
def string_finder(string_to_find, list_of_strings):
    for i in range(len(list_of_strings)):
        if list_of_strings[i] == string_to_find:
            return i
    return None

#Main login function
#Note 1: after 5 failed password attempts, user should be locked out temporarily- currently just discards username due to pycharm limitations (add timelock or discard this feature)
#Note 2 (technical): usernames and passwords stored as text files, depending on implementation might need a different file type
#Note 3: no username/password security (update if time allows and after full implementation of login page)
#Note 4: currently inputs are cancelled by typing "x", this will be superceded by a button in full implementation
#Note 5: code most likely breaks if username/password file does not exist (this will possibly cease to be an issue at full implementation, else add error handling)
#Note 6 (technical): No error handling implemented (should implement at some point later on)
def login():
    login_status = None
    while login_status == None:
        user_username = input("Enter your username (X to cancel):\n")
        if user_username == "X" or user_username == "x":
            login_status = False
            continue
        with open("login_usernames.txt") as file:
            lines = file.read().splitlines()
            username_found = string_finder(user_username, lines)
            if username_found == None:
                print("Error- username not found.")
                continue
            else:
                with open("login_passwords.txt") as file:
                    lines = file.read().splitlines()
                    file_password = lines[username_found]
                    password_attempts = 5
                    while password_attempts > 0:
                        user_password = input("Enter your password:\n")
                        if user_password == file_password:
                            login_status = True
                            break
                        else:
                            password_attempts -= 1
                            if password_attempts > 0:
                                print("Error- incorrect password.")
                            else:
                                print("Error- too many incorrect passwords were entered. You have been temporarily locked out.")
                                login_status = False
                                continue
    return login_status

#Main function to create a new account
#Note 7: Are username/password requirements sensible, or do any need to be added/removed?
def create_account():
    account_created_status = None
    while account_created_status == None:
        new_username = input("Enter new username (or X to cancel):\n")
        if new_username == "x" or new_username == "X":
            account_created_status = False
            continue
        username_is_valid = True
        if len(new_username) < 8:
            print("Error: usernames must contain at least 8 characters.")
            username_is_valid = False
        elif len(new_username) > 30:
            print("Error: usernames must contain no more than 30 characters.")
            username_is_valid = False
        else:
            with open("login_usernames.txt") as file:
                lines = file.read().splitlines()
                username_found = string_finder(new_username, lines)
                if not username_found == None:
                    print("Error- that username is already in use.")
                    username_is_valid = False
        if username_is_valid == True:
            new_username = new_username + "\n"
            chosen_password = choose_password()
            if chosen_password:
                chosen_password = chosen_password + "\n"
                with open("login_usernames.txt", "a") as file:
                    file.write(new_username)
                with open("login_passwords.txt", "a") as file:
                    file.write(chosen_password)
                account_created_status = True
                continue
    return account_created_status

#Function for choosing a password (called as part of create_account)
def choose_password():
    while True:
        new_password = input("Enter new password (or X to cancel):\n")
        if new_password == "x" or new_password == "X":
            return None
        password_is_valid = True
        if len(new_password) < 8:
            print("Error: password must contain at least 8 characters.")
            password_is_valid = False
        elif len(new_password) > 30:
            print("Error: password must contain no more than 30 characters.")
            password_is_valid = False
        else:
            lowercase_present = False
            uppercase_present = False
            number_present = False
            special_present = False
            for i in new_password:
                if i in "qwertyuiopasdfghjklzxcvbnm":
                    lowercase_present = True
                elif i in "QWERTYUIOPASDFGHJKLZXCVBNM":
                    uppercase_present = True
                elif i in "1234567890":
                    number_present = True
                else:
                    special_present = True
            if lowercase_present == False:
                print("Error- password must contain at least 1 lowercase letter.")
                password_is_valid = False
            if uppercase_present == False:
                print("Error- password must contain at least 1 uppercase letter.")
                password_is_valid = False
            if number_present == False:
                print("Error- password must contain at least 1 number.")
                password_is_valid = False
            if special_present == False:
                print("Error- password must contain at least 1 special character.")
                password_is_valid = False
        if password_is_valid:
            confirm_password = input("Confirm password:\n")
            if new_password == confirm_password:
                return new_password
            else:
                print("Error- passwords do not match.")

#Main function, called on startup
#Note 8: This function will be replaced with buttons on full implementation
def main():
    test_select = input("Do you have a user account? Y/N: ")
    while True:
        if test_select == "Y" or test_select == "y":
            login_status = login()
            if login_status == True:
                print("Login successful.")
            else:
                print("Login failed.")
            break
        elif test_select == "N" or test_select == "n":
            print("You will need to create a Username and Password.")
            print("Usernames must contain 8-30 characters and must be unique.")
            print("Passwords must contain 8-30 characters and must contain at least 1 lower case letter, upper case letter, number, and special character.")
            account_created_status = create_account()
            if account_created_status:
                print("Account successfully created!.")
            else:
                print("Account creation failed.")
            break
        else:
            print("Error- please enter the character Y or N.")

if __name__ == "__main__":
    main()
