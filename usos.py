#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Wykrywa zmiany ocen w USOS'ie i reaguje na nie.

Przykladowy config:

login = 'PESEL'
haslo = 'HASLO'
plik_bazy = 'oceny.sqlite'
def powiadom(str):
  return subprocess.call(['/home/g/sms.orange.pl, "docelowy-nr", str, 
    "login", "haslo"])

BY d33tah, LICENSED UNDER WTFPL.
"""

import pysqlite2.dbapi2 as sqlite3
import mechanize
from lxml import html

from config import *

def t(obj): return obj.text_content()

class USOS_Baza:
  
  
  def __init__(self,plik_bazy):
    self.conn = sqlite3.connect(plik_bazy)
    self.c = self.conn.cursor()
    self.c.execute("CREATE TABLE IF NOT EXISTS oceny " +
        "(przedmiot TEXT UNIQUE, ocena TEXT)")
    self.conn.commit()

    
  def pobierz(self,ocena):
    print "Pobieram"
    ret = self.c.execute("SELECT * FROM oceny WHERE przedmiot = ?",
                                            (ocena.przedmiot,)).fetchone()
    if ret:
      return USOS_Ocena(ret[0],ret[1])
  
  def dodaj(self,ocena):
    print "Dodaje"
    self.c.execute("INSERT INTO oceny VALUES (?,?)",
                            (ocena.przedmiot,ocena.oceny))
    self.conn.commit()

  def aktualizuj(self,ocena):
    print "Updatuje"
    self.c.execute("UPDATE oceny SET ocena = ? WHERE przedmiot = ?",
                            (ocena.oceny,ocena.przedmiot))
    self.conn.commit()

class USOS_Ocena:
  
  
  def __init__(self,przedmiot,oceny):
    self.przedmiot = przedmiot
    self.oceny = oceny
    
  def __eq__(obj1,obj2):
    if isinstance(obj1,USOS_Ocena) and isinstance(obj2,USOS_Ocena):
      return obj1.przedmiot == obj2.przedmiot \
                  and obj1.oceny == obj2.oceny
    else:
      return False
                  
  def __str__(self):
    return "<USOS_Ocena: %s || %s>" % (self.przedmiot,self.oceny)


class USOS:
    
  
  def __init__(self,login,haslo):
    
    self.mech = mechanize.Browser()
    self.mech.set_handle_robots(False)
    #user_agent = 'Mozilla/4.0 (compatible; MSIE 6.0; ' + \
    #'Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)'
    #self.mech.addheaders += [("User-agent",user_agent)]
    self.mech.addheaders += [("Accept-Language",
                                      'pl-PL,pl;q=0.8,en-US;q=0.6,en;q=0.4')]
    
    self.mech.open('https://logowanie.uni.lodz.pl/cas/login')
    self.mech.select_form(nr=0)
    self.mech.form['username']=login
    self.mech.form['password']=haslo
    self.mech.submit()
    
    if self.mech.response().read().find('Udane logowanie') == -1:
      raise Exception('Blad logowania po stronie CAS.')
    
    #w sumie nie wiem po co to tu, ale bez tego zapytania nie dziala :P
    self.mech.open('https://usosweb.uni.lodz.pl/kontroler.php?'+
                              '_action=actionx:logowaniecas/index()')
    
  def pobierz_oceny(self):
  
    ret = []
  
    self.mech.open('https://usosweb.uni.lodz.pl/kontroler.php?'+
                              '_action=actionx:dla_stud/studia/oceny/index()')
    response = self.mech.response().read()
    if response.find("Zalogowany: <b") == -1:
      raise Exception('Blad logowania po stronie USOS.')
    
    tree = html.fromstring(response)
    for ocena in tree.xpath('//table [@class = "grey"]//tr'):
      
      if len(ocena) != 4:
        continue
      if t(ocena[2][0]) == '(brak ocen)':
        continue
      
      o_przedmiot = t(ocena[0][0])
      #o_kod = t(ocena[0][1])
      
      o_oceny = ''
      for frag in ocena[2]:
        o_oceny += '%s: %s; ' % ( t(frag[0]), t(frag[1]) )
        
      ret.append(USOS_Ocena(o_przedmiot,o_oceny))
    return ret
    
if __name__ == '__main__':    
  baza = USOS_Baza(plik_bazy)
  usos = USOS(login,haslo)
  oceny = usos.pobierz_oceny()
  for ocena in oceny:
    z_bazy = baza.pobierz(ocena)
    if z_bazy == ocena:
      continue
    elif z_bazy==None:
      baza.dodaj(ocena)
    else:
      baza.aktualizuj(ocena)
    powiadom("USOS: %s: %s" % (ocena.przedmiot,ocena.oceny)) 