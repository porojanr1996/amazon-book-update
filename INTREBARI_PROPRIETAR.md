# Întrebări pentru Proprietar - Înainte de Development

## 📋 Scop
Aceste întrebări ajută la clarificarea cerințelor și preferințelor înainte de implementare finală, pentru a evita modificări costisitoare mai târziu.

---

## 🔐 1. Acces și Credențiale

### Google Sheets
- [ ] **Ai deja un Google Sheet creat sau trebuie să-l creez eu?**
- [ ] **Ai acces la Google Cloud Console pentru setup API?** (dacă nu, îți pot ghida pas cu pas)
- [ ] **Preferi să configurezi tu Google Sheets API sau vrei să o fac eu?**
- [ ] **Câți oameni vor avea acces la Google Sheet?** (pentru a seta permisiunile corect)

### Website
- [ ] **Cine va avea acces la website?** (public, doar echipa, doar tu, cu parolă?)
- [ ] **Vrei autentificare/login pentru website sau este public?**
- [ ] **Ai deja hosting/server sau trebuie să recomand/configurez eu?**

---

## 📊 2. Structura Google Sheets

### Format Date
- [ ] **Ai deja un Google Sheet cu cărți sau trebuie să-l creez de la zero?**
- [ ] **Ce structură preferi pentru Sheet?** (pot sugera o structură optimă)
- [ ] **Câte cărți aproximativ vei urmări?** (10, 50, 100, 500+?)
- [ ] **Vrei să adaug coloane pentru informații suplimentare?** (preț, reviews, copertă, etc.)

### Categorii
- [ ] **Ce categorii exacte vei folosi?** (ex: Fiction US, Fiction UK, Mafia Romance US, etc.)
- [ ] **Câte categorii aproximativ?**
- [ ] **O carte poate aparține la mai multe categorii sau doar una?**

### Calculare Medii
- [ ] **Vrei să calculez automat media BSR în Google Sheets sau doar să scriu valorile zilnice?**
- [ ] **Vrei și alte statistici?** (min, max, trend, etc.)

---

## 🌐 3. Website și Design

### Accesibilitate
- [ ] **Website-ul trebuie să fie public sau doar pentru echipă?**
- [ ] **Vrei subdomeniu specific?** (ex: `ranks.novamediamarketing.com` sau `www.novamediamarketing.com/ranks`)
- [ ] **Ai preferințe pentru URL?** (ex: `/ranks`, `/bsr-tracker`, `/dashboard`)

### Design și Branding
- [ ] **Ai un logo sau brand colors pe care să le folosesc?**
- [ ] **Vrei design custom sau pot folosi design-ul standard pe care l-am creat?**
- [ ] **Ai exemple de website-uri care îți plac ca stil?**
- [ ] **Vrei dark mode sau doar light mode?**

### Funcționalități Website
- [ ] **Vrei export date?** (CSV, Excel, PDF?)
- [ ] **Vrei notificări când BSR-ul se schimbă semnificativ?** (email, Slack, etc.)
- [ ] **Vrei comparație între cărți?** (side-by-side charts)
- [ ] **Vrei search/filtrare pe nume autor sau carte?**

---

## 🤖 4. Automatizare și Scraping

### Programare
- [ ] **Ora 10:00 AM (Bucharest time) este ok sau preferi altă oră?**
- [ ] **Vrei să ruleze și în weekend sau doar în zilele lucrătoare?**
- [ ] **Ce faci dacă scraping-ul eșuează într-o zi?** (retry automat, notificare, etc.)

### Rate Limiting
- [ ] **Câte cărți aproximativ vei urmări?** (pentru a calcula timpul de scraping)
- [ ] **Ești ok cu delay-ul de 2 secunde între request-uri?** (pentru a evita blocarea de la Amazon)
- [ ] **Vrei să adaug proxy-uri dacă Amazon blochează request-urile?**

### Gestionare Erori
- [ ] **Ce vrei să se întâmple dacă o carte nu mai există pe Amazon?** (skip, notificare, marcare în Sheet?)
- [ ] **Vrei log-uri detaliate sau doar erori importante?**

---

## 📈 5. Grafice și Vizualizări

### Grafice
- [ ] **Ce tipuri de grafice preferi?** (line chart, bar chart, area chart?)
- [ ] **Vrei să văd evoluția pentru o carte individuală sau doar media generală?**
- [ ] **Vrei să pot compara mai multe cărți simultan pe același grafic?**

### Filtre Timp
- [ ] **Filtrele propuse sunt ok?** (7 zile, 30 zile, 90 zile, 1 an, all time)
- [ ] **Vrei și alte perioade?** (ex: ultimele 3 zile, ultimele 6 luni)

### Top Rankings
- [ ] **Top 50 este suficient sau vrei Top 100/Top 200?**
- [ ] **Vrei să pot sorta și descrescător?** (worst performers)
- [ ] **Vrei să pot vedea istoricul pentru o carte specifică?**

---

## 💰 6. Costuri și Hosting

### Budget
- [ ] **Care este bugetul tău pentru hosting?** ($5-10/lună, $10-20/lună, $20+/lună?)
- [ ] **Preferi soluție gratuită (cu limitări) sau plătești pentru hosting dedicat?**
- [ ] **Vrei estimare de costuri pentru primul an?**

### Provider Preferințe
- [ ] **Ai deja un provider de hosting preferat?** (DigitalOcean, AWS, Google Cloud, etc.)
- [ ] **Ai cont deja creat sau trebuie să-l creez eu?**
- [ ] **Vrei să gestionez eu hosting-ul sau preferi să-l gestionezi tu?**

---

## 🔧 7. Funcționalități Bonus (Nice to Have)

### Informații Suplimentare
- [ ] **Vrei să extrag și prețul de pe Amazon?** (poate adăuga complexitate)
- [ ] **Vrei să extrag numărul de reviews?** (poate adăuga complexitate)
- [ ] **Vrei să extrag coperta cărții automat?** (din Google Sheets sau direct de pe Amazon)
- [ ] **Vrei să extrag și alte informații?** (publication date, page count, etc.)

### Notificări
- [ ] **Vrei notificări email când BSR-ul se schimbă semnificativ?**
- [ ] **Vrei notificări pentru erori în scraping?**
- [ ] **Vrei dashboard cu alert-uri pentru cărți cu BSR în creștere/scădere?**

### Export și Rapoarte
- [ ] **Vrei export automat zilnic/săptămânal?** (CSV, Excel, PDF?)
- [ ] **Vrei rapoarte automate?** (email cu summary săptămânal?)

---

## 🚀 8. Deployment și Mentenanță

### Deployment
- [ ] **Vrei să fac eu deployment-ul complet sau preferi să-l faci tu cu ghidul meu?**
- [ ] **Ai acces la server/VPS sau trebuie să recomand și să configurez eu?**
- [ ] **Vrei SSL certificate?** (HTTPS - recomandat pentru securitate)

### Mentenanță
- [ ] **Cine va gestiona mentenanța zilnică?** (tu, echipa ta, sau eu?)
- [ ] **Vrei contract de mentenanță sau doar setup inițial?**
- [ ] **Ce faci dacă Amazon schimbă structura paginii și scraping-ul nu mai funcționează?** (vrei să actualizez eu sau preferi să o faci tu?)

### Backup
- [ ] **Vrei backup automat al datelor?** (Google Sheets are backup automat, dar poți vrea backup suplimentar)
- [ ] **Cât de important este să nu pierzi date istorice?**

---

## 📱 9. Acces și Utilizare

### Utilizatori
- [ ] **Câți oameni vor folosi sistemul?** (1, 5, 10, 50+?)
- [ ] **Vor accesa de pe desktop, mobile, sau ambele?**
- [ ] **Vrei versiune mobile-friendly optimizată?**

### Training
- [ ] **Vrei documentație pentru utilizatori?**
- [ ] **Vrei training session sau doar documentație scrisă?**
- [ ] **Cine va adăuga cărți noi în Google Sheet?** (tu, echipa, automat?)

---

## ⚡ 10. Prioritate și Timeline

### Prioritate Funcționalități
- [ ] **Care sunt funcționalitățile MUST HAVE vs NICE TO HAVE?**
- [ ] **Ce funcționalități pot fi adăugate mai târziu în faza 2?**

### Timeline
- [ ] **Când ai nevoie de sistemul funcțional?** (urgent, 1 săptămână, 1 lună?)
- [ ] **Vrei să începem cu MVP (Minimum Viable Product) și apoi adăugăm funcționalități?**
- [ ] **Ai deadline-uri specifice?**

---

## 🎯 11. Suport și Documentație

### Documentație
- [ ] **Ce tip de documentație preferi?** (README simplu, video tutorial, ghid pas cu pas?)
- [ ] **Vrei documentație în română sau engleză?**
- [ ] **Vrei comentarii în cod sau doar documentație externă?**

### Suport
- [ ] **Cum preferi să comunicăm?** (email, Slack, WhatsApp, etc.)
- [ ] **Vrei suport continuu sau doar la setup?**

---

## ✅ Checklist Final

După ce răspunzi la aceste întrebări, voi putea:

- [ ] **Clarifica toate cerințele**
- [ ] **Estima timpul exact de implementare**
- [ ] **Estima costurile exacte**
- [ ] **Crea un plan de implementare detaliat**
- [ ] **Evita modificări costisitoare mai târziu**

---

## 📝 Notă Importantă

**Nu trebuie să răspunzi la TOATE întrebările acum!** 

Poți răspunde doar la cele care sunt importante pentru tine, iar pentru restul pot folosi valori default sau pot decide eu bazat pe best practices.

**Prioritizează:**
1. ✅ Acces și credențiale (secțiunea 1)
2. ✅ Structura Google Sheets (secțiunea 2) 
3. ✅ Website și design (secțiunea 3)
4. ✅ Automatizare (secțiunea 4)

Restul pot fi discutate pe parcurs! 🚀

