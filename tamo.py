import time

from flask import session, render_template, request, redirect
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from app import app
from config import authorised_clients, enableTest
from utils import issue_jwt
from log import log

log("Getting chromedriver", "TAMO")
chromedriver = ChromeDriverManager().install()


@app.route('/tamo/login', methods=['GET', 'POST'])
def tamo_login():
    try:
        session['our_redirect_uri']
    except:
        return "Bad request", 400
    if request.method == 'GET':
        return render_template('tamo_login.html', appId=authorised_clients[session['our_client_id']]['name'],
                               error=request.args.get('error'))
    else:
        username = request.form['username']
        password = request.form['password']
        if username == password and enableTest:
            session['name'] = password
            return issue_jwt(password, session['our_client_id'])
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(chromedriver, options=chrome_options)

        driver.get("https://dienynas.tamo.lt/Prisijungimas/Login")

        driver.find_element_by_id('UserName').send_keys(username)
        driver.find_element_by_id('Password').send_keys(password)

        driver.find_element_by_css_selector('.c_btn.submit').click()

        if driver.current_url != 'https://dienynas.tamo.lt/DashboardStudents' and \
                driver.current_url != 'https://dienynas.tamo.lt/Dashboard':
            driver.close()
            return redirect("/tamo/login?error=1")

        # user_data = {
        #     "full_name": raw_data['displayName'],
        #     "first_name": raw_data['givenName'],
        #     "last_name": raw_data['surname'],
        #     "raw_title": raw_title,
        #     "grade": grade,
        #     "roles": roles,
        #     # Other data that can not be gathered from Microsoft
        #     "dependants": []
        # }
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
            if "kodas=MOK" in href and "kodas=MOKMOK" not in href:
                duomenu_btn = driver.find_element_by_xpath("//a[contains(@href, '/Profilis/index/')]")
                driver.get(duomenu_btn.get_attribute('href'))

                time.sleep(0.5)
                colmd6 = driver.find_elements_by_css_selector("div.col-md-6.readonly_input")

                raw_name = colmd6[0].text.split(" ")
                grade = colmd6[1].text
                first_name = "".join(raw_name[1:])
                last_name = raw_name[0]
                full_name = first_name + " " + last_name
                roles += ["student"]
            if "kodas=TEVGLO" in href:
                duomenu_btn = driver.find_element_by_xpath("//a[contains(@href, '/Profilis/Vaiko')]")
                vaiko_duomenu_href = duomenu_btn.get_attribute('href')

                tevo_duomenu_btn = driver.find_element_by_xpath(
                    "//a[contains(@href, '/Naudotojas/PrisijungimoDuomenysProfile/')]")
                tevo_duomenu_href = tevo_duomenu_btn.get_attribute('href')
                driver.get(tevo_duomenu_href)
                time.sleep(0.5)
                first_name = driver.find_element_by_id("Vardas").get_attribute('value')
                last_name = driver.find_element_by_id("Pavarde").get_attribute('value')
                full_name = first_name + " " + last_name
                grade = ""

                driver.get(vaiko_duomenu_href)
                time.sleep(0.5)
                colmd6 = driver.find_elements_by_css_selector("div.col-md-6.readonly_input")

                raw_name = colmd6[0].text.split(" ")
                child_grade = colmd6[1].text
                child_first_name = "".join(raw_name[1:])
                child_last_name = raw_name[0]
                child_full_name = child_first_name + " " + child_last_name
                roles += ["parent"]
                dependants += [{
                    "full_name": child_full_name,
                    "first_name": child_first_name,
                    "last_name": child_last_name,
                    "grade": child_grade
                }]
            if "kodas=MOKMOK" in href:
                full_name = driver.find_element_by_css_selector(
                    'html > body.container > div#header_section.row > div.col-md-14 >'
                    ' div > div > div.header-box > div > div > div > div > div').text.split(" ")
                first_name = full_name[:-1]
                last_name = full_name[-1]
                grade = ""
                roles += ["teacher"]

        driver.close()

        try:
            user_data = {
                "full_name": full_name,
                "first_name": first_name,
                "last_name": last_name,
                "raw_title": "",
                "grade": grade,
                "roles": roles,
                "dependants": dependants
            }
            session['user_data'] = user_data
            return issue_jwt(user_data, session['our_client_id'])
        except:
            return redirect("/tamo/login?error=2")
