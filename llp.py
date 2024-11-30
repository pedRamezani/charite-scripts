from bs4 import BeautifulSoup
import requests
import webbrowser

from getpass import getpass
import re
import sys


numberRegEx = re.compile(r'^\d+$')
chariteRegEx = re.compile(r'^.+@charite\.de$')


def printLlpObj(llpObj, index):
    outputString = f'{str(index + 1)}) {llpObj["title"].rstrip()}:\n'
    for i, date in enumerate(llpObj["dates"]):
        if not date.string:
            # Einzeltermin
            outputString += f'\t{str(i + 1)}. {date.string};\n'
        else:
            # Mehrfachtermin
            outputString += f'\t{str(i + 1)}. MEHRFACHTERMIN '
            for info in date.strings:
                outputString += info
            outputString += ";\n"
    print(outputString)


def chooseTermin(output):
    for index, llpObj in enumerate(output):
        printLlpObj(llpObj, index)

    inputString1 = input(
        "Wähle dein Tutorium (Nummer) oder gib etwas anderes ein um abzubrechen: ")
    match = numberRegEx.match(inputString1)
    if match:
        num1 = int(inputString1)
        if num1 < 1 or num1 > len(output):
            print('Diese Nummer ist leider nicht gültig.')
            return ''
        printLlpObj(output[num1 - 1], num1 - 1)
        inputString2 = input(
            "Wähle dein Termin (Nummer) oder gib etwas anderes ein um abzubrechen: ")
        match = numberRegEx.match(inputString2)
        if match:
            num2 = int(inputString2)
            if num2 < 1 or num2 > len(output[num1 - 1]['links']):
                print('Diese Nummer ist leider nicht gültig.')
                return ''
            else:
                return output[num1 - 1]["links"][num2 - 1]
        else:
            print('Buchung abgebrochen.')
            return ''
    else:
        print('Buchung abgebrochen.')
        return ''


def login(session, user, password):
    r = session.get("https://lernziele.charite.de/zend/sym/bridge/to/ssoStudi")
    loginUrl = BeautifulSoup(r.text, 'html.parser').find(
        'form', id="options")["action"]
    loginSite = session.post(
        loginUrl, data={'Username': user, 'Password': password})
    return not (BeautifulSoup(loginSite.text, 'html.parser').title.string == "Anmelden")


def printTutStats(session):
    r = session.get(
        "https://lernziele.charite.de/zend/tutorien/eigene/anbieterId/1")
    stats = BeautifulSoup(r.text, 'html.parser').find('div', id="content").find_all(
        string=re.compile('^Teilgenommene.+$'), recursive=False)
    for line in stats:
        print(line)
    print('85% der angegebenen Einheiten reichen bereits aus, um zu bestehen (25,5/51)\n')


def printBookedTut(bookedTableRows):
    for index, tableRow in enumerate(bookedTableRows):
        td = tableRow.find_all('td')
        title = td[0].strong.string
        dates = tableRow.find_all('b', 'aktiv')
        llpObj = {}
        llpObj["title"] = title
        llpObj["dates"] = dates
        printLlpObj(llpObj, index)


def getTerminObjs(correctTableRows):
    output = []

    for tableRow in correctTableRows:
        td = tableRow.find_all('td')
        title = td[0].strong.string
        dates = tableRow.find_all('b', 'notice')

        links = []
        for date in dates:
            links.append(
                f'https://lernziele.charite.de{date.find_previous("a", href=True)["href"]}')

        llpObj = {}
        llpObj["title"] = title
        llpObj["dates"] = dates
        llpObj["links"] = links

        output.append(llpObj)

    return output


def book(session, url):
    print(
        f'\nVersuche nun über den folgenden Link den Termin zu buchen:\n{url}')
    tut = session.get(url)
    bookForm = BeautifulSoup(tut.text, 'html.parser').find(
        'form', method="POST")
    if not bookForm:
        print("Dieses Tutorium lässt sich nicht über dieses Tool buchen. \n")
        print("Klick am besten auf den Link oben, um den Termin im Browser zu betrachten.")
    else:
        bookLink = "https://lernziele.charite.de" + bookForm['action']
        b = session.post(bookLink, data={'buchen': 'true'})
        if b.status_code == 200:
            print("Das Tutorium konnte erfolgreich gebucht werden. Schau am besten noch einmal nach um sicher zu gehen.")
        else:
            print("Fehler. Das Tutorium konnte nicht gebucht werden. Schau am besten noch einmal nach um sicher zu gehen.")


def main():
    print("Willkommen beim LLp Tutorienbuchservice!")
    session = requests.Session()

    retry = True
    while retry:
        user = input("Bitte gib dein Benutzernamen in Email-Format ein: ")
        if not chariteRegEx.match(user):
            user += "@charite.de"
        password = getpass("Bitte gib dein Passwort ein und drück Enter. ")
        logedIn = login(session, user, password)
        if not logedIn:
            retry = input(
                "Falsche Email oder Kennwort. Wiederholen? y/n ").lower() == 'y'
        else:
            retry = False
    print(f'{"Anmeldung erfolgreich" if logedIn else ""}\n')

    r = session.get(
        "https://lernziele.charite.de/zend/tutorien/uebersicht/anbieterId/1?idGruppe=alle")
    if r.status_code != 200:
        print("API endpoint didn't return 200 OK.")
        sys.exit(1)

    html = r.text
    soup = BeautifulSoup(html, 'html.parser')

    table = soup.find('table', 'tblstd')
    tableRows = table.find_all('tr')
    correctTableRows = []

    bookedTableRows = []
    for tableRow in tableRows:
        if len(tableRow.find_all('b', 'notice')) != 0:
            correctTableRows.append(tableRow)
        if len(tableRow.find_all('b', 'aktiv')) != 0 and logedIn:
            bookedTableRows.append(tableRow)

    if logedIn:
        printTutStats(session)
        if len(bookedTableRows) != 0:
            print("Folgende Termine wurden bereits gebucht: \n")
            printBookedTut(bookedTableRows)
        else:
            print("Es sind zur Zeit keine Tutorien unter diesem Account gebucht.")

    if len(correctTableRows) == 0:
        print("Konnte keine freien Tutorien finden.")
        sys.exit(1)
    else:
        print("Folgende Termine konnten gefunden werden: \n")

    url = chooseTermin(getTerminObjs(correctTableRows))
    if not url:
        sys.exit(1)
    else:
        if logedIn:
            book(session, url)
        else:
            webbrowser.open(url, new=0, autoraise=True)


if __name__ == "__main__":
    main()
