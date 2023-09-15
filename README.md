# id.licejus.lt

## Trumpas backstory
Darydamas kelis projektus, kuriems prireikė autentifikuoti liceistus sugalvojau padaryti šią sistemą aplamai palengvinti autentifikavimą ir sumažinti sketchy php formų kiekį.

## Kaipgi man pasinaudoti šituo daiktu?
Iš esmės veikimo principas paremtas [OAuth2](https://oauth.net/2/) standartu, bet kai kurios pagal mane nereikalingos dalys tiesiog nebuvo implementuotos (maniau, kad nereikalinga / tingėjau - pagrindinis dalykas, ko trūksta, tai normalaus public key handlingo), todėl nežinau, ar bus galima naudotis kažkokiais jau egzistuojančiais library.

Naudosiu sąvokas taip:
Useris: web browseris, naudotojas
Aplikacija: jusų aplikacija
ID: autentifikavimo sistema (id.licejus.lt)

Veikimo principas toks:
 1. Useris redirectinamas į https://id.licejus.lt/v2.0/authorize?client_id=JUSU_CLIENT_ID&redirect_uri=JUSU_REDIRECT_URI
 2. Useris ID autentifikuojasi vienaip ar kitaip
 3. Useris ID redirectinamas i JUSU_REDIRECT_URI?id_token=JWT_TOKEN (grąžinamas JWT tokenas, gali būti kad ir localhost standalone aplikacijoms)
 4. Jūsų aplikacija patikrina JWT tokeną (apie tai vėliau)

### Kaip gauti JUSU_CLIENT_ID ir JUSU_REDIRECT_URI?
Jie gaunami registravus aplikaciją [čia](https://id.licejus.lt/dashboard). Client ID yra unikalus ir negali kartotis, todėl nebus dviejų aplikacijų su tokiu pačiu Client ID. Redirect URI gali būti keli, svarbu, kad bent vienas, naudojamas /v2.0/authorize būtų tame saraše.

### Kas tas JWT tokenas ir kaip man jį patvirtinti?
Plačiau apie JWT tokenus rasite [čia](https://jwt.io/introduction).
Kadangi JWT tokenai yra *signed*, todėl aš juos čia ir naudoju. Dekoduoti patariu naudoti library. Jame rasite šiuos duomenis:
1. full_name: Vardas ir pavardė
2. name: Lygus `full_name`. Paliktas dėl backwards compatibility.
3. first_name: Vardas / vardai
4. last_name: Pavardė
5. raw_title: Pavadinimas, prirašytas prie žmogaus (pvz. `ia klasės mokinys` ar `xyz dalyko mokytojas` gaunami iš MSFT, o TAMO generuojami ant vietos, mokytojai bus tik `mokytojas` ar `mokytoja`, o tėvai `tėvas` ar `motina`)
6. grade: Klasė, formatuota `IIIa` (jei ne tėvas ar mokytojas, tada tuščia)
7. roles: Listas žmogaus rolių (Gali būti ir teacher ir parent viename.) Galimi variantai: `teacher`, `parent`, `student`
8. dependants: Jei tėvas, tai bus listas vaikų duomenų, formatuoti `{"full_name": child_full_name, "first_name": child_first_name, "last_name": child_last_name, "grade": child_grade}`
9. iss: Issuer - visada bus `id.licejus.lt`
10. aud: Audience - visada bus `JUSU_CLIENT_ID`
11. exp: Expiration - Po šio laiko (UTC unix millis) tokenas nebeturėtų būti priimtas. Tai visada bus laikas, kada useris autentifikavosi + 10 min.

JWT headeryje visada rasite `'kid': '87c0615c19dd98fdc301615d522601f5'`. 

JWT tokenas pasirašytas SHA256 algoritmu. Public raktą tikrinimui rasite https://id.licejus.lt/v2.0/keys. Raktas yra PEM formatu. **Raktas gali keistis!** Tai nereiškia, kad reikia prieš kiekvieną autentifikaciją siųstis jį iš naujo, nes raktas bus keičiamas tik kažkokio breacho ar pan. atveju, tad tiesiog padarykite, kad raktą aplikacija parsisiųstų po restarto.

### Kaip atjungti userį?
Userį šiaip turėtumėte atjungti naudodami savo aplikacijos sistemas, bet jei kažkodėl reikėtų atjungti userį nuo visos ID sistemos, tai galima padaryti userį redirectinus i https://id.licejus.lt/v2.0/logout?redirect=URI (redirect'as nebutinas, bet tada tiesiog numes į id.licejus.lt)

### Kilus klausimams, rašykite [me@nojus.dev](mailto:me+docs@nojus.dev)