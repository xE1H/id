import shutil

from flask import session, render_template, request, redirect
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

from app import app
from config import enable_test
from log import log
from utils import issue_jwt, get_app_display_name

log("Getting chromedriver", "TAMO")

if (shutil.which('chrome') or shutil.which('chromium')) and shutil.which('chromedriver'):
    chromedriver = "chromedriver"
else:
    chromedriver = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()


@app.route('/tamo/login', methods=['GET', 'POST'])
def tamo_login():
    try:
        session['our_redirect_uri']
    except BaseException:
        return "Bad request", 400
    if request.method == 'GET':
        return render_template(
            'tamo_login.html',
            appId=get_app_display_name(
                session['our_client_id']),
            error=request.args.get('error'),
            message=request.args.get('message'))
    else:
        username = request.form['username']
        password = request.form['password']
        if username == password and enable_test:
            session['name'] = password
            return issue_jwt(password, session['our_client_id'])
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(chromedriver, options=chrome_options)

        driver.get("https://dienynas.tamo.lt/Prisijungimas/Login")

        # Output html to check if correct
        print(driver.page_source)

        driver.find_element_by_id('UserName').send_keys(username)
        driver.find_element_by_id('Password').send_keys(password)

        driver.find_element_by_css_selector('.c_btn.submit').click()

        if not driver.current_url.startswith('https://dienynas.tamo.lt/DashboardStudents') and \
                not driver.current_url.startswith('https://dienynas.tamo.lt/Dashboard'):
            driver.close()
            return redirect("/tamo/login?error=1")

        roles = []
        dependants = []

        data = driver.find_elements_by_css_selector(".c_select_options > a")
        # Save current uri to go back
        data = [i.get_attribute('href') for i in data]

        for i in data:
            href = i
            if "istaigosId=1435" not in href:
                continue
            # Get irasoId from URI
            driver.get(href)
            raw_title = ""
            if "kodas=MOK" in href and "kodas=MOKMOK" not in href:
                duomenu_btn = driver.find_element_by_xpath(
                    "//a[contains(@href, '/Profilis/index/')]")
                driver.get(duomenu_btn.get_attribute('href'))

                WebDriverWait(
                    driver, 3).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'div.col-md-6.readonly_input')))

                colmd6 = driver.find_elements_by_css_selector(
                    "div.col-md-6.readonly_input")

                raw_name = colmd6[0].text.split(" ")
                grade = colmd6[1].text
                first_name = "".join(raw_name[1:])
                last_name = raw_name[0]
                full_name = first_name + " " + last_name
                raw_title = grade.lower() + " klasės mokin" + \
                            "ys" if first_name.endswith("s") else "ė"
                roles += ["student"]
            if "kodas=TEVGLO" in href:
                duomenu_btn = driver.find_element_by_xpath(
                    "//a[contains(@href, '/Profilis/Vaiko')]")
                vaiko_duomenu_href = duomenu_btn.get_attribute('href')

                tevo_duomenu_btn = driver.find_element_by_xpath(
                    "//a[contains(@href, '/Naudotojas/PrisijungimoDuomenysProfile/')]")
                tevo_duomenu_href = tevo_duomenu_btn.get_attribute('href')
                driver.get(tevo_duomenu_href)

                WebDriverWait(
                    driver, 3).until(
                    EC.presence_of_element_located(
                        (By.ID, 'Vardas')))

                first_name = driver.find_element_by_id(
                    "Vardas").get_attribute('value')
                last_name = driver.find_element_by_id(
                    "Pavarde").get_attribute('value')
                full_name = first_name + " " + last_name
                grade = ""

                driver.get(vaiko_duomenu_href)
                WebDriverWait(
                    driver, 3).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'div.col-md-6.readonly_input')))

                colmd6 = driver.find_elements_by_css_selector(
                    "div.col-md-6.readonly_input")

                raw_name = colmd6[0].text.split(" ")
                child_grade = colmd6[1].text
                child_first_name = "".join(raw_name[1:])
                child_last_name = raw_name[0]
                child_full_name = child_first_name + " " + child_last_name
                roles += ["parent"]
                raw_title = "tėvas" if first_name.endswith("s") else "motina"
                dependants += [
                    {
                        "full_name": child_full_name,
                        "first_name": child_first_name,
                        "last_name": child_last_name,
                        "grade": child_grade,
                        "raw_title": child_grade.lower() +
                                     " klasės mokin" +
                                     "ys" if child_first_name.endswith("s") else "ė",
                    }]
            if "kodas=MOKMOK" in href:
                full_name = driver.find_element_by_css_selector(
                    'html > body.container > div#header_section.row > div.col-md-14 >'
                    ' div > div > div.header-box > div > div > div > div > div').text.split(" ")
                first_name = " ".join(full_name[:-1])
                last_name = full_name[-1]
                grade = ""
                raw_title = "mokytoja" + \
                            "s" if first_name.endswith("s") else ""
                roles += ["teacher"]

        driver.close()

        try:
            user_data = {
                "name": full_name,
                "full_name": full_name,
                "first_name": first_name,
                "last_name": last_name,
                "raw_title": raw_title,
                "grade": grade,
                "roles": roles,
                "dependants": dependants
            }
            session['user_data'] = user_data
            return issue_jwt(user_data, session['our_client_id'])
        except Exception as e:
            return redirect("/tamo/login?error=2&message=" + str(e))
