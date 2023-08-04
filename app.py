import undetected_chromedriver as uc
import requests
import sys, os, time, json
from pick import pick


class Udemy:
    def __init__(self):
        self.udemy_url = "https://www.udemy.com/"
        self.udemy_login_url = "https://www.udemy.com/join/login-popup/?locale=tr_TR&response_type=html&next=https%3A%2F%2Fwww.udemy.com%2F"
        self.udemy_users_api = "https://www.udemy.com/api-2.0/courses/{self.id}/students/?None=2&fields%5Buser%5D=%40default%2Ccompletion_ratio%2Cenrollment_date%2Cis_organization_enrollment%2Clast_accessed%2Cquestion_count%2Cquestion_answer_count&ordering=-enrollment_date"
        self.udemy_message_url = "https://www.udemy.com/instructor/communication/messages/compose/user"
    
    def get_cookies(self, only_read=False, get=False):
        try:
            with open("cookies.json", "r") as c:
                cookies_json = json.load(c)
                if get: return cookies_json
                if not only_read:
                    title = "Do you want to clear old data?"
                    options = ["Yes, (remove and login)", "No"]
                    option, index = pick(options, title)
                    if index == 0:
                        self.__clear_cookies()
                        self.get_cookies()
                    else:
                        return

        except:
            if only_read or get:
                return
            driver = uc.Chrome()
            driver.get(self.udemy_login_url)
            while True:
                time.sleep(2)
                if driver.current_url == self.udemy_url:
                    cookies_json = driver.get_cookies()
                    driver.close()
                    break
                
            with open("cookies.json", "w") as c:
                json.dump(cookies_json, c)
        self.session = requests.Session()
        for cookie in cookies_json:
            self.session.cookies.set(cookie["name"], cookie["value"])

    def __clear_cookies():
        with open("cookies.json", "w") as c:
            pass

    def get_users(self):
        try:
            with open("users.json", "r", encoding="utf-8") as users:
                self.user_profiles = json.load(users)
        except:
            self.user_profiles = {}

    def write_users(self):
        with open("users.json", "w", encoding="utf-8") as users_file:
            json.dump(self.user_profiles, users_file)

    def remove_from_users(self, user_id):
        self.user_profiles.pop(user_id)
        self.write_users()

    def restore_users(self):
        with open("backup.json", "r", encoding="utf-8") as backup:
            self.user_profiles = json.load(backup)
        self.write_users()
        input("Users restored! Press enter to return menu")


class UdemyUsers(Udemy):
    def __init__(self, id):
        super().__init__()
        self.fetch_limit = 100
        self.id = id
        self.get_users()

    def __get_url(self, limit=None):
        return f"{self.udemy_users_api}&page={1 if limit else int(len(self.user_profiles)/self.fetch_limit)+1}&page_size={self.fetch_limit}&q="

    def __progress_bar(self, progress, total, user):
        sys.stdout.write("\r")
        sys.stdout.write(
            f"Completed: {int(progress/total*100):>3}% | ({progress}/{total} Users) Last: {user}              "
        )
        sys.stdout.flush()

    def get_all_user_profiles(self):
        self.get_cookies(only_read=True)
        self.get_messages_cookies()
        print("Please wait..")
        limit = -1
        while True:
            if len(self.user_profiles) == limit:
                with open("backup.json", "w", encoding="utf-8") as backup:
                    json.dump(self.user_profiles, backup)
                print("Completed!")
                break
            r = self.session.get(self.__get_url())
            time.sleep(5)
            if r.status_code == 200:
                data = r.json()
                if limit == -1:
                    limit = data["count"]
                results = data["results"]
                for user in results:
                    self.user_profiles[user["id"]] = user["title"]
                self.url = self.__get_url(limit=limit)
                self.write_users()
                self.__progress_bar(len(self.user_profiles), limit, user["title"])
            else:
                print(
                    f"ERROR ({r.status_code}): {r.json().get('detail')}, Wait 10 second"
                )
                time.sleep(11)


class UdemyMessage(Udemy):
    def __init__(self):
        super().__init__()
        self.get_users()

    def __progress_bar(self, progress, total, user):
        sys.stdout.write("\r")
        sys.stdout.write(f"Sent: {round(progress/total*100):>3}% | ({progress}/{total}) User: {user}              ")   
        sys.stdout.flush()

    def send_message(self):
        self.get_cookies(only_read=True)
        count = int(input("Enter count value (press enter for default): ") or "0")
        if count == 0:
            count = len(self.user_profiles)
        with open("message.txt", "r", encoding="utf-8") as message:
            content = message.read()
            if not content:
                input("Message.txt is empty. Please write a message (HTML)")
                return
        
        driver = uc.Chrome()
        driver.set_window_position(-10000,0)
        driver.get(self.udemy_url)
        for cookie in self.get_cookies(get=True):
            driver.add_cookie(cookie)

        number = 0
        user_profiles_items = self.user_profiles.copy().items()
        for id, name in user_profiles_items:
            url = f"{self.udemy_message_url}/{id}/"
            if number == count:
                driver.close()
                break
            number += 1
            driver.get(url)
            try:
                if url == driver.current_url:
                    time.sleep(2.5)
                    driver.execute_script(f"""document.querySelector('.ProseMirror.rt-scaffolding > p').innerHTML = "{content}";""")
                    time.sleep(1)
                    driver.execute_script("""document.querySelector('.ud-btn-primary').click();""")
                    time.sleep(1)
                    self.remove_from_users(id)
            except Exception as e:
                pass
                #print(e)
            self.__progress_bar(number, count, name)
            time.sleep(1)


if __name__ == "__main__":
    udemy = Udemy()
    print(udemy.udemy_url)
    udemy_message = UdemyMessage()
    udemy_users = UdemyUsers(id=4035876)
    title = "Please choose a process"
    options = [
        "Login with Udemy",
        "Fetch users",
        "Restore users",
        "Send message",
        "Exit",
    ]
    while True:
        os.system("cls")
        option, index = pick(options, title)
        if index == 0:
            udemy_users.get_cookies()
        elif index == 1:
            udemy_users.get_all_user_profiles()
        elif index == 2:
            udemy.restore_users()
        elif index == 3:
            udemy_message.send_message()
        else:
            sys.exit()
