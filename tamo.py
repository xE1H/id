from flask import session, render_template, request, redirect
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from __main__ import app
from config import authorised_clients, enableTest
from utils import issue_jwt


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
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        driver.get("https://dienynas.tamo.lt/Prisijungimas/Login")

        driver.find_element_by_id('UserName').send_keys(username)
        driver.find_element_by_id('Password').send_keys(password)

        driver.find_element_by_css_selector('.c_btn.submit').click()

        if driver.current_url != 'https://dienynas.tamo.lt/DashboardStudents' and \
                driver.current_url != 'https://dienynas.tamo.lt/Dashboard':
            driver.close()
            return redirect("/tamo/login?error=1")

        schoolName = driver.find_element_by_css_selector(
            'html > body.container > div#top_section.row > div.col-md-14 >'
            ' div.row.top_section_back > div.col-md-10 > span').text

        if schoolName != 'Vilniaus licėjus':
            driver.close()
            return redirect("/tamo/login?error=2")

        name = driver.find_element_by_css_selector(
            'html > body.container > div#header_section.row > div.col-md-14 >'
            ' div > div > div.header-box > div > div > div > div > div').text

        driver.close()
        session['name'] = name

        return issue_jwt(name, session['our_client_id'])
