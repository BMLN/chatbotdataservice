import unittest
from os import path, environ
from tempfile import TemporaryDirectory
from io import StringIO

from typing import override



try:
    from src.processing import build_dataset
except:
    pass






class BuildTest(unittest.TestCase):
    
    @override
    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

        with open(path.join(self.tmpdir.name, "testdata.csv"), "w", encoding="utf-8") as f:
            f.write(""",issue_key,problem_raw,solution_raw
0,SWELIB-3018,"Problem bei Anmeldung

Sehr geehrte Damen und Herren,

ich bin von der FOM und möchte das SAP Miktrozertifikat bearbeiten. Beim anmelden, kam leider die Fehlermeldung das der Benutzername oder das Kennwort falsch seien. Ich habe alles mehrfach und korrekt eingegeben, leider ohne Erfolg.

Hallo Raphael,

ich habe dein Passwort für das SAP-System auf das Initialkennwort “placeholder“ zurückgesetzt, probiere nochmal dich hiermit anzumelden und setze dir danach ein neues Passwort.

Guten Tag,

könnten sie mein Passwort erneut zurücksetzen? Leider kann ich mich wieder nicht anmelden, obwohl ich eigentlich das richtige Passwort benutze. Hab auch jede Mögliche andere Kombination ausprobiert, leider funktioniert das aber auch nicht.

Hallo Raphael,

ich habe dein Passwort erneut zurückgesetzt.

Das Passwort ist wieder “placeholder“.

LG Dein WLIB-Team.

Die Anmeldung funktioniert jetzt. Ich bin auf den Account gegangen und sehe das dort schon Aktivität war obwohl ich noch nichts gemacht habe. Vielleicht auch der Grund dafür das mein Passwort durch die Person die meinen Account benutzt immer wieder zurückgesetzt wird. In meiner Mail steht drin das ich den Nutzer: LEARN-301 habe, deswegen habe ich nichts vertauscht. Wie ist das weitere Vorgehen?

Hallo Raphael,

ein Learn-User wird immer nur einem Nutzer zugewiesen.

Du solltest die einzige Person sein die Zugriff auf dem Learn User auf dem entsprechenden Mandanten hat.

Es kann höchstens sein, dass eine Person zufällig genau in dem Moment den Learn User 301 auf einen anderen Mandanten zugewiesen bekommen hat und sich ggf. ausversehen auf deinem Mandanten eingeloggt hat.

Es sollten jetzt aber keine Probleme mehr für dich auftreten und auch nur du hast Zugriff auf den Account.

LG dein WLIB Team.

Hallo Zusammen,

dadurch das jemand voher auf meinem Account drauf war und teilweise schon Aufgaben erledigt hat, wurden in dem Studenmonitor bei einer Fallstudie etwas rot makiert, was ich nicht mehr ausbessern kann. Dabei handelt es sich um ein Produkt was ich wie in den Videos beschrieben anlegen wollte. Nachdem ich das Produkt Entgültig anlegen wollte hieß es, das das Produkt bereits unter dem Namen “CHLK1301” von LEARN-301 erstellt wurde, was ich aber nicht war. Meinen Entwurf habe ich dann aber anders genannt , nur leider wird dadurch das Rote Kreuz nicht überschrieben. Bei dem voher angelegten Produkt kann ich leider auch nichts mehr ändern.

Hallo Raphael,

Der Studentenmonitor befindet sich noch in einer Betaversion und soll lediglich als Orientierung dienen. 

Solange du keine Fehlermeldung bei der weiteren Bearbeitung erhältst kannst du einfach mit der Bearbeitung fortfahren.

In deinem Fall kannst du sofern das Produkt richtig angelegt wurde ggf. mit dem bereits erstellten Produkt weiterarbeiten.

Alternativ kann ich dir auch einen neuen Account zur Verfügung stellen bei dem noch nichts angelegt wurde.

LG.

Guten Tag,

mein Account + Passwort funktioniert für das Modul Rechnungswesen & Controlling leider n","Hallo Raphael,
ich habe Deinen Account entsperrt und das Passwort wieder auf:
placeholder

zurückgesetzt. Viel Erfolg bei der weiteren Bearbeitung!
Beste Grüße
Tim - WLIB-Support

Hallo Raphael,
ich habe dir einen neuen Zugang erstellt. Wahrscheinlich wurde dein bisheriger Zugang durch Verwechslungen mit dem Mandant von anderen Nutzern gesperrt. Gib bitte Bescheid, welche Fallstudien du bisher bearbeitet hast.
Nutze ab jetzt bitte LEARN-452 auf dem Mandant 301.
Das Kennwort lautet wieder:
placeholder
Beste Grüße
Tim - WLIB-Support"
1,SWELIB-3154,"Unterstützung bei Kreditorenrechnung und Sachkonto

Hallo liebes Support-Team,

ich benötige bitte Unterstützung zu zwei Aufgaben.
Ich habe eine Kreditorenrechnung gemäß Anleitung aus dem Video angelegt, geprüft und gebucht. Allerdings zeigt mir der Studentenmonitor an, dass ich nichts gesichert habe. Ich habe den Buchungsbeleg der Lieferantenrechnung überprüft und kann keinen Fehler erkennen. Könnten Sie mir bitte helfen herauszufinden, woran das liegt?

Zudem wird mir bei einer weiteren Aufgabe angezeigt, dass ich das Sachkonto nicht korrekt eingetragen habe, obwohl ich exakt das Sachkonto verwendet habe, das im Video genannt wurde. Auch hier benötige ich Unterstützung, um den Fehler zu finden.

Die entsprechende Fehlermeldung habe ich im Anhang beigefügt.

Vielen Dank im Voraus für Ihre Hilfe!

!Bild 11-28-25 um 15.07.png|thumbnail!

!Bild 11-28-25 um 15.15.png|thumbnail!

{color:#172B4D}Hallo Tim,{color}{color:#172B4D}{color}   
  
{color:#172B4D} Danke für deine Antwort. Leider ist die Email im Spam gelandet, weshalb ich die Nachricht erst jetzt sehe. Könntest du mir diesen Screenshot erneut schicken? Ich würde dann einfach weiter machen und bei weiteren Problemen gerne auf euch zu kommen.{color}{color:#172B4D}{color}   
  
{color:#172B4D} Beste Grüße{color}  
{color:#172B4D} Wijdan Hermi{color}

---!AUTOMATED MESSAGE! CURRENTLY IN TESTING! ONLY CONTAINS END-TO-END COURSE DATA!---
{""Antwort"":""Die E-Mail mit allen wichtigen Informationen zum Kursstart, Zugangsdaten für die SAP-Systeme und Hinweise zur VPN-Freischaltung wurde erneut bereitgestellt und erklärt.""}

Hallo Tim, 

 
  

 vielen Dank für den Screenshot. Ich habe eine weitere Frage zu einer anderen Aufgabe. Ich wollte den Buchungsbeleg 1800001090 stornieren, aber das System lässt mich nicht. Daher habe ich einen anderen Beleg (1800001091) storniert, um zu sehen, ob das möglich ist. Der Beleg 1800001091 ließ sich stornieren. 

 
  

 Könntest du mir helfen, das Problem mit dem Beleg 1800001090 zu lösen? 

 
  

 Mit freundlichen Grüßen, 

 Wijdan Hermi  

 
  
{quote} 
Am 1/9/26 um 14:59 schrieb We Learn in Bits Hilfeportal <jira@iis-ls.atlassian.net>:{color:#333333}{color}{color:#999999}{color} 
 
 
   
 {color:#333333}{color}{quote}

---!AUTOMATED MESSAGE! CURRENTLY IN TESTING! ONLY CONTAINS END-TO-END COURSE DATA!---
{""Antwort"":""Es wurde noch keine endgültige Lösung dokumentiert. Bitte senden Sie einen Screenshot der Fehlermeldung und prüfen Sie, ob die Buchungsbelegnummer 1800001090 korrekt ist. Ohne weitere Informationen können wir die genaue Vorgehensweise zur Stornierung uut nicht erläutern.""}

Hallo, 

 
  

 anbei schicke ich dir den Screenshot, den ich in meiner letzten E-Mail vergessen habe, damit du das Problem besser nachvollziehen kannst. 

 
  

 Mit freundlichen Grüßen, 

 Wijdan Hermi 
  
 
  
 
 
{quote} {quote}

!5D215651-1520-4641-BEB8-2966AB217F1B-Bild 1-14-26 um 16.50.png|thumbnail!

---!AUTOMATED MESSAGE! CURRENTLY IN TESTING! ONLY CONTAINS END-TO-END COURSE DAT","Hallo Wijdan,

bezüglich Schritt 5 handelt es sich um einen Anzeigefehler im Studierendenmonitor, dort hast du alles richtig bearbeitet. Beim zweiten Screenshots handelt es sich um die Herausforderung Kreditorenbuchhaltung, diese wird im R&C Kurs nicht bearbeitet. Die Fallstudie hast Du (siehe Screenshot) bereits abgeschlossen.


!{9BCA2BE4-95A4-4669-8963-E0C9154CDCE9}-20251129-191544.png|width=1021,alt=""{9BCA2BE4-95A4-4669-8963-E0C9154CDCE9}-20251129-191544.png""!

Beste Grüße
Tim - WLIB-Support

Hallo Wijdan,
Gerne, anbei der Screenshot:

!{9BCA2BE4-95A4-4669-8963-E0C9154CDCE9}-20251129-191544 (b9414e05-febb-4629-a84b-269e12899513).png|width=1021,alt=""{9BCA2BE4-95A4-4669-8963-E0C9154CDCE9}-20251129-191544.png""!

Beste Grüße
Tim - WLIB-Support"
""")



    @unittest.skipIf(not environ.get("DEEPINFRA_API_TOKEN"), "env var not set")
    def test(self):
        to_test = build_dataset.process_csv


        #args
        args = [
            path.join(self.tmpdir.name, "testdata.csv"),
            path.join(self.tmpdir.name, "output.csv")
        ]

        #test
        to_test(*args)

        with open(path.join(self.tmpdir.name, "output.csv"), encoding="utf-8") as f:
            self.assertIn("problem_raw,solution_raw,problem,solution", f.readline())