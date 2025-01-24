import threading
import json
import random
from datetime import datetime
import copy


max_users = 2

account_locks = {}

# load data from JSON file
def load_data(filename):
    filename_json = filename + ".json"
    try:
        with open(filename_json, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("File not found, creating a new one.")
        with open(filename_json, 'w+') as f:
            # json.dump({filename: {}}, f, indent=4)
            json.dump({}, f)
        with open(filename_json, "r") as file:
            return json.load(file)

# update data in JSON file 
def save_data(data, filename):
    existing_data = load_data(filename)

    if(existing_data != {}):
        existing_data[filename].update(data[filename])
    else:
        existing_data.update(data)

    with open(filename+".json", 'w') as f:
        json.dump(existing_data, f, indent=4)

class UserAccount(threading.Thread):
    def __init__(self, username, action, amount=0, target_user=None):
        threading.Thread.__init__(self)
        self.username = username
        self.action = action
        self.amount = amount
        self.target_user = target_user  # for transfer money
        self.data = load_data(filename=username)

        # lock for each account
        self._ensure_account_lock(self.username)
        if self.target_user:
            self._ensure_account_lock(self.target_user)

    def _ensure_account_lock(self, username):
        if username not in account_locks:
            account_locks[username] = threading.Lock()

    def run(self):
        self.create_account()
        if self.action == "check_balance":  # no need to lock
            self.check_balance()
        elif self.action == "deposit":
            self.deposit()
        elif self.action == "withdraw":
            self.withdraw()
        elif self.action == "transfer":
            self.transfer()

    def create_account(self):
        """ create account with initial balance """
        if self.username not in self.data:
            self.data[self.username] = {"balance": self.amount, "transactions": []}
            with account_locks[self.username]:
                save_data(self.data, self.username)
            print(f"Account for {self.username} created with balance {self.amount}")

    def check_balance(self):
        """ show the wallet balance """
        self.data = load_data(self.username)
        account = self.data[self.username]
        if account:
            print(f"Current balance of {self.username}: {account['balance']}")
        else:
            print(f"Account for {self.username} does not exist.")

    def deposit(self):
        self.data = load_data(self.username)
        account = self.data[self.username]
        temp = copy.deepcopy(account)
        if account:
            with account_locks[self.username]:
                account["balance"] += self.amount
                account["transactions"].append({"type": "deposit", "amount": self.amount, "status": True, "timestamp": datetime.now().isoformat()})
                try:
                    save_data(self.data, self.username)
                except Exception:
                    print(f"[Deposit] for {self.username} failed.")
                    account = temp
                    account["transactions"].append({"type": "deposit", "amount": self.amount, "status": False, "timestamp": datetime.now().isoformat()})
                    self.data[self.username] = account
                    save_data(self.data, self.username)
                    return 0
            print(f"Deposited {self.amount} to {self.username}'s account.")
        else:
            print(f"Account for {self.username} does not exist.")

    def withdraw(self):
        self.data = load_data(self.username)
        account = self.data[self.username]
        temp = copy.deepcopy(account)
        if account:
            with account_locks[self.username]:
                if account["balance"] >= self.amount:
                    account["balance"] -= self.amount
                    account["transactions"].append({"type": "withdraw", "amount": self.amount, "status": True, "timestamp": datetime.now().isoformat()})
                    try:
                        save_data(self.data, self.username)
                    except Exception:
                        print(f"[Withdraw] for {self.username} failed.")
                        account = temp
                        account["transactions"].append({"type": "withdraw", "amount": self.amount, "status": False, "timestamp": datetime.now().isoformat()})
                        self.data[self.username] = account
                        save_data(self.data, self.username)
                        return 0
                    print(f"Withdrew {self.amount} from {self.username}'s account.")
                else:
                    print(f"Insufficient balance for {self.username}.")
        else:
            print(f"Account for {self.username} does not exist.")

    def transfer(self):
        print(f"[SELF USER - TARGET USER] {self.username} - {self.target_user}")
        try:
            self.data = load_data(self.username)
        except Exception:
            print(f"Could not load data for {self.username}. Run the program again!")
            return
        account_from = self.data[self.username]
        temp_from = copy.deepcopy(account_from)
        try:
            target_data = load_data(self.target_user)
        except Exception:
            print(f"Could not load data for {self.target_user}.")
            return
        account_to = target_data[self.target_user]
        temp_to = copy.deepcopy(account_to)
        if account_from and account_to:
            lock1, lock2 = self._get_locks()
            with lock1:
                print("lock1 acquired")
                with lock2:
                    print("lock2 acquired")
                    if account_from["balance"] >= self.amount:
                        account_from["balance"] -= self.amount
                        account_to["balance"] += self.amount
                        account_from["transactions"].append({"type": "transfer", "amount": self.amount, "to": self.target_user, "status": True, "timestamp": datetime.now().isoformat()})
                        account_to["transactions"].append({"type": "transfer", "amount": self.amount, "from": self.username, "status": True, "timestamp": datetime.now().isoformat()})
                        try:
                            save_data(self.data, self.username)
                            save_data(target_data, self.target_user)
                            # raise Exception
                        except Exception:
                            print(f"[Transfer] from {self.username} to {self.target_user} failed.")
                            account_from = temp_from
                            account_to = temp_to
                            account_from["transactions"].append({"type": "transfer", "amount": self.amount, "to": self.target_user, "status": False, "timestamp": datetime.now().isoformat()})
                            self.data[self.username] = account_from
                            target_data[self.target_user] = account_to
                            save_data(self.data, self.username)
                            save_data(target_data, self.target_user)
                            return 0
                        print(f"Transferred {self.amount} from {self.username} to {self.target_user}.")
                    else:
                        print(f"Insufficient balance in {self.username}'s account.")
        else:
            print(f"One or both accounts do not exist.")

    def _get_locks(self):
        if self.username < self.target_user:
            return account_locks[self.username], account_locks[self.target_user]
        else:
            return account_locks[self.target_user], account_locks[self.username]

# random user choices
def users_actions():
    actions = ["deposit", "withdraw", "transfer", "check_balance"]
    # actions = ["transfer"]

    users = []

    for i in range(max_users):
        username = f"user{i}"
        action = random.choice(actions)
        print(f"This is action of user{i}: {action}")
        amount = random.randint(1, 500)
        random_num = i
        while random_num == i:
            random_num = random.randint(0, max_users - 1)
        target_user = f"user{random_num}" if action == "transfer" else None
        if(target_user != None):
            print(f"[TARGET USER] for user{i}: {target_user}")
        
        user_thread = UserAccount(username, action, amount, target_user)
        users.append(user_thread)
    
    return users

def run_system():
    users = users_actions()

    for user in users:
        user.start()

    for user in users:
        user.join()

if __name__ == "__main__":
    run_system()
