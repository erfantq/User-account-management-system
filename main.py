import threading
import json
import random
from datetime import datetime
import copy

# قفل برای همگام‌سازی
# lock = threading.Lock()
max_users = 20

account_locks = {}

# تابعی برای بارگذاری داده‌ها از فایل
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
        
# ذخیره داده‌ها در فایل JSON (بدون پاک کردن داده‌های قبلی)
def save_data(data, filename):
    # بارگذاری داده‌های موجود از فایل
    existing_data = load_data(filename)
    
    print(f"existing data before change: {existing_data}")
    # ادغام داده‌های جدید با داده‌های موجود
    print("\n")

    print(f"this is data[filename]: {data[filename]}")

    if(existing_data != {}):
        existing_data[filename].update(data[filename])
    else:
        existing_data.update(data)
    print("\n")

    print(f"existing data after change: {existing_data}")

    
    # ذخیره داده‌ها در فایل
    with open(filename+".json", 'w') as f:
        json.dump(existing_data, f, indent=4)


# کلاس برای ایجاد هر رشته کاربر
class UserAccount(threading.Thread):
    def __init__(self, username, action, amount=0, target_user=None):
        threading.Thread.__init__(self)
        self.username = username
        self.action = action
        self.amount = amount
        self.target_user = target_user  # برای انتقال وجه
        self.data = load_data(filename=username)

        # ایجاد قفل برای هر حساب
        self._ensure_account_lock(self.username)
        if self.target_user:
            self._ensure_account_lock(self.target_user)

    def _ensure_account_lock(self, username):
        """ بررسی و ایجاد قفل برای هر حساب کاربری در صورت لزوم """
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
        # ایجاد حساب جدید با موجودی اولیه
        # print(f"This is self.data: {self.data}")
        if self.username not in self.data:
            self.data[self.username] = {"balance": self.amount, "transactions": []}
            with account_locks[self.username]:
                save_data(self.data, self.username)
            print(f"Account for {self.username} created with balance {self.amount}")
        # else:
        #     print(f"Account for {self.username} already exists.")

    def check_balance(self):
        # show the wallet balance
        self.data = load_data(self.username)
        account = self.data[self.username]
        if account:
            print(f"Current balance of {self.username}: {account['balance']}")
        else:
            print(f"Account for {self.username} does not exist.")

    def deposit(self):
        # واریز وجه
        self.data = load_data(self.username)
        account = self.data[self.username]
        temp = copy.deepcopy(account)
        if account:
            with account_locks[self.username]:
                account["balance"] += self.amount
                account["transactions"].append({"type": "deposit", "amount": self.amount, "status": True, "timestamp": datetime.now().isoformat()})
                try:
                    # print(f"This is data for deposit with {self.amount} and {self.username}: {self.data}")
                    save_data(self.data, self.username)
                except Exception:
                    print(f"[Deposit] for {self.username} failed.")
                    account = temp
                    account["transactions"].append({"type": "deposit", "amount": self.amount, "status": False, "timestamp": datetime.now().isoformat()})
                    save_data(self.data, self.username)
                    return 0
            print(f"Deposited {self.amount} to {self.username}'s account.")
        else:
            print(f"Account for {self.username} does not exist.")

    def withdraw(self):
        # برداشت وجه
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
                        save_data(self.data, self.username)
                        return 0
                    print(f"Withdrew {self.amount} from {self.username}'s account.")
                else:
                    print(f"Insufficient balance for {self.username}.")
        else:
            print(f"Account for {self.username} does not exist.")

    def transfer(self):
        # انتقال وجه
        self.data = load_data(self.username)
        account_from = self.data[self.username]
        temp_from = copy.deepcopy(account_from)
        target_data = load_data(self.target_user) 
        account_to = target_data[self.target_user]
        temp_to = copy.deepcopy(account_to)
        if account_from and account_to:
            lock1, lock2 = self._get_locks(account_from, account_to)
            with lock1:
                with lock2:
                    if account_from["balance"] >= self.amount:
                        account_from["balance"] -= self.amount
                        account_to["balance"] += self.amount
                        account_from["transactions"].append({"type": "transfer", "amount": self.amount, "to": self.target_user, "status": True, "timestamp": datetime.now().isoformat()})
                        account_to["transactions"].append({"type": "transfer", "amount": self.amount, "from": self.username, "status": True, "timestamp": datetime.now().isoformat()})
                        try:
                            save_data(self.data, self.username)
                            save_data(target_data, self.target_user)
                        except Exception:
                            print(f"[Transfer] from {self.username} to {self.target_user} failed.")
                            account_from = temp_from
                            account_to = temp_to
                            account_from["transactions"].append({"type": "transfer", "amount": self.amount, "to": self.target_user, "status": False, "timestamp": datetime.now().isoformat()})
                            save_data(self.data, self.username)
                            save_data(target_data, self.target_user)
                            return 0
                        print(f"Transferred {self.amount} from {self.username} to {self.target_user}.")
                    else:
                        print(f"Insufficient balance in {self.username}'s account.")
        else:
            print(f"One or both accounts do not exist.")

    def _get_locks(self, account_from, account_to):
        """ دریافت قفل‌ها به ترتیب مشخص برای جلوگیری از بن‌بست """
        if self.username < self.target_user:
            return account_locks[self.username], account_locks[self.target_user]
        else:
            return account_locks[self.target_user], account_locks[self.username]
# تابعی برای ایجاد کاربران تصادفی
def users_actions():
    # actions = ["deposit", "withdraw", "transfer", "check_balance"]
    actions = ["transfer"]

    users = []

    # ایجاد 20 کاربر به صورت استاتیک
    for i in range(max_users):
        username = f"user{i}"
        action = random.choice(actions)
        amount = random.randint(1, 500)
        target_user = f"user{random.randint(1, 20)}" if action == "transfer" else None
        
        user_thread = UserAccount(username, action, amount, target_user)
        users.append(user_thread)
    
    return users

# اجرای برنامه
def run_system():
    users = users_actions()

    # اجرای تمام تردها
    for user in users:
        user.start()

    # منتظر بمانید تا همه تردها تمام شوند
    for user in users:
        user.join()

if __name__ == "__main__":
    run_system()
