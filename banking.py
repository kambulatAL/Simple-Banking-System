import random
import sqlite3


class Database:
    def __new__(cls, db_name):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Database, cls).__new__(cls)
        return cls.instance

    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.curr = self.conn.cursor()

    def create_card_table(self):
        self.curr.execute("""CREATE TABLE IF NOT EXISTS card (
                                id INTEGER PRIMARY KEY,
                                number TEXT,
                                pin TEXT,
                                balance INTEGER DEFAULT 0);""")
        self.conn.commit()

    def find_card(self, card_num):
        self.curr.execute(f"""
                            SELECT * 
                            FROM card
                            WHERE number = '{card_num}';""")
        return self.curr.fetchone()

    def add_card(self, card_num, pin, balance):
        self.curr.execute(f"""
                            INSERT INTO card(number, pin, balance)
                            VALUES('{card_num}','{pin}',{balance});""")
        self.conn.commit()

    def add_income(self, income, card_num):
        self.curr.execute(f"""
                            UPDATE card
                            SET balance = balance + {income}
                            where number = '{card_num}';""")
        self.conn.commit()

    def transfer_money(self, money, from_card, to_card):
        self.curr.executescript(f"""
                            UPDATE card
                            SET balance = balance - {money}
                            where number = '{from_card}';
                            
                            UPDATE card
                            SET balance = balance + {money}
                            where number = '{to_card}';""")
        self.conn.commit()

    def close_acc(self, user_id):
        self.curr.execute(f"""
                            DELETE FROM card
                            WHERE id = '{user_id}'""")
        self.conn.commit()


class BankAccount:
    ACC_ID_LENGTH = 9
    PINCODE_LENGTH = 4
    BIN = '400000'

    def __init__(self):
        self._credit_card = self.BIN
        self._pin_code = None
        self._balance = 0

    @staticmethod
    def luhn_algorithm(card):
        acc_card = list(map(int, card))

        for i in range(0, len(acc_card), 2):
            acc_card[i] *= 2
            if acc_card[i] > 9:
                acc_card[i] -= 9
        control_num = sum(acc_card)

        return control_num

    def find_checksum(self, card):
        control_num = self.luhn_algorithm(card)
        for i in range(10):
            if (control_num + i) % 10 == 0:
                return i
        return -1

    def gen_requisites(self):
        self.credit_card = self.credit_card + ''.join([str(random.randrange(10)) for _ in range(self.ACC_ID_LENGTH)])
        checksum = self.find_checksum(self.credit_card)
        if checksum == -1: return False
        self.credit_card += str(checksum)

        self.pin_code = ''.join([str(random.randrange(10)) for _ in range(self.PINCODE_LENGTH)])
        return True

    @property
    def credit_card(self):
        return self._credit_card

    @credit_card.setter
    def credit_card(self, val):
        self._credit_card = val

    @property
    def pin_code(self):
        return self._pin_code

    @pin_code.setter
    def pin_code(self, val):
        self._pin_code = val

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, val):
        self._balance = val


class Bank:
    def __init__(self, db):
        self.db = db

    def check_card_in_db(self, card_num):
        return self.db.find_card(card_num) is not None

    def create_account(self):
        acc = BankAccount()
        while not acc.gen_requisites() or self.check_card_in_db(acc.credit_card):
            acc.credit_card = acc.BIN
        # print(self.db.curr.execute("select * from card;").fetchall())
        self.db.add_card(acc.credit_card, acc.pin_code, acc.balance)

        print('Your card has been created')
        print(f'Your card number:\n{acc.credit_card}')
        print(f'Your card PIN:\n{acc.pin_code}')

    def log_in(self):
        print('Enter your card number:')
        card_num = input().strip()
        print('Enter your PIN:')
        pin = input().strip()

        account = self.db.find_card(card_num)
        if account is None or account[2] != pin:
            print('Wrong card number or PIN!')
            return False, None
        else:
            print('You have successfully logged in!')
            return True, account

    def transfer_money(self, card_num):
        print('Transfer')
        print('Enter card number:')
        to_card = input().strip()
        account = self.db.find_card(card_num)

        if BankAccount().luhn_algorithm(to_card) % 10 != 0:
            print('Probably you made a mistake in the card number. Please try again!')
            return
        elif not self.check_card_in_db(to_card):
            print('Such a card does not exist.')
            return
        elif to_card == account[1]:
            print('You can\'t transfer money to the same account!')
            return

        print('Enter how much money you want to transfer:')
        amount = int(input())
        if amount > account[3]:
            print('Not enough money!')
            return

        self.db.transfer_money(amount, account[1], to_card)
        print('Success!')

    def process_logged_usr(self, account):
        print(*['1. Balance', '2. Add income',
                '3. Do transfer', '4. Close account',
                '5. Log out', '0. Exit'], sep='\n')

        inp_code = int(input())
        if inp_code == 1:
            print(f'Balance: {account[3]}')
        elif inp_code == 2:
            print('Enter income:')
            income = int(input())
            self.db.add_income(income, account[1])
            print('Income was added!')
        elif inp_code == 3:
            self.transfer_money(account[1])
        elif inp_code == 4:
            self.db.close_acc(account[0])
            print('The account has been closed!')
        elif inp_code == 5:
            print('You have successfully logged out!')
        elif inp_code == 0:
            print('Bye!')

        return inp_code

    def start_system(self):
        while True:
            print(*['1. Create an account', '2. Log into account', '0. Exit'], sep='\n')

            inp_code = int(input())
            if inp_code == 0:
                print('Bye!')
                return
            elif inp_code == 1:
                self.create_account()
            elif inp_code == 2:
                is_logged, acc = self.log_in()
                while is_logged:
                    logged_inp_code = self.process_logged_usr(acc)
                    if logged_inp_code == 5:
                        is_logged = False
                    elif logged_inp_code == 0:
                        return


database = Database('card.s3db')
database.create_card_table()

bank = Bank(database)
bank.start_system()
