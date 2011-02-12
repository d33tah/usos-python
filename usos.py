#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wykrywa zmiany ocen w USOS'ie i reaguje na nie.

Przykladowy config:

import subprocess #zeby moc uruchomic proces
login = 'PESEL'
haslo = 'HASLO'
plik_bazy = 'oceny.sqlite'
def powiadom(str):
  return subprocess.call(['/home/g/sms.orange.pl, "docelowy-nr", str, 
    "login", "haslo"])

BY d33tah, LICENSED UNDER CREATIVE COMMONS BY-SA LICENSE.
"""

import pickle
from sys import exit
import pysqlite2.dbapi2 as sqlite3
import mechanize
from lxml import html

from config import *

def t(obj): return obj.text_content()
def debug(str): pass
#def debug(str): print str
#def powiadom(str): print str

class USOS_Baza:
  
  
  def __init__(self,plik_bazy):
    self.conn = sqlite3.connect(plik_bazy)
    self.c = self.conn.cursor()
    self.c.execute("CREATE TABLE IF NOT EXISTS oceny " +
        "(przedmiot TEXT, kod TEXT, ocena TEXT)")
    self.c.execute("CREATE TABLE IF NOT EXISTS config " +
        "(klucz TEXT UNIQUE, tresc BLOB)")
    self.conn.commit()

    
  def pobierz(self,ocena):
    debug("Pobieram %s" % ocena.przedmiot)
    ret = self.c.execute("SELECT * FROM oceny WHERE przedmiot = ? AND kod = ?",
                                            (ocena.przedmiot,ocena.kod)).fetchone()
    if ret:
      return USOS_Ocena(ret[0],ret[1],ret[2])
  
  def dodaj(self,ocena):
    debug("Dodaje %s" % ocena.przedmiot)
    self.c.execute("INSERT INTO oceny VALUES (?,?,?)",
                            (ocena.przedmiot,ocena.kod,ocena.oceny))
    self.conn.commit()

  def aktualizuj(self,ocena):
    debug("Updatuje %s" % ocena.przedmiot)
    self.c.execute("UPDATE oceny SET ocena = ? WHERE przedmiot = ? AND kod = ?",
                            (ocena.oceny,ocena.przedmiot,ocena.kod))
    self.conn.commit()

  def ustaw_login(self,mech):
    debug("Pobieram login...");
    ret = self.c.execute("SELECT * FROM config WHERE klucz = ?", ("cookies", )).fetchone()

    if ret:
      mech._ua_handlers['_cookies'].cookiejar = pickle.loads(str(ret[1]))
      return True
    else:
      return False

  def zapisz_login(self,mech):
    debug("Zapisuje login...");
    tresc = pickle.dumps(mech._ua_handlers['_cookies'].cookiejar)
    ret = self.c.execute("SELECT * FROM config WHERE klucz = ?", ("cookies", )).fetchone()
    if ret:
      debug("Juz cos jest.")
      self.c.execute("UPDATE config SET tresc = ? WHERE klucz = ?", (tresc, "cookies")).fetchone()
      self.conn.commit()
      return True
    else:
      debug("Jeszcze nic nie ma...")
      self.c.execute("INSERT INTO config VALUES (?,?)" , ("cookies", tresc))
      self.conn.commit()
      return True

class USOS_Ocena:
  
  
  def __init__(self,przedmiot,kod,oceny):
    self.przedmiot = przedmiot
    self.kod = kod
    self.oceny = oceny
    
  def __eq__(obj1,obj2):
    if isinstance(obj1,USOS_Ocena) and isinstance(obj2,USOS_Ocena):
      return obj1.przedmiot == obj2.przedmiot \
                  and obj1.kod == obj2.kod \
                  and obj1.oceny == obj2.oceny
    else:
      return False
                  
  def __str__(self):
    return "<USOS_Ocena: przedmiot='%s' kod='%s' oceny='%s'>" % (self.przedmiot,self.kod,self.oceny)


class USOS:
    
  
  def __init__(self):
    
    self.mech = mechanize.Browser()
    self.mech.set_handle_robots(False)
    #user_agent = 'Mozilla/4.0 (compatible; MSIE 6.0; ' + \
    #'Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)'
    #self.mech.addheaders += [("User-agent",user_agent)]
    self.mech.addheaders += [("Accept-Language",
                                      'pl-PL,pl;q=0.8,en-US;q=0.6,en;q=0.4')]
    
  def login(self,login,haslo):
    
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
      o_kod = t(ocena[1][0])
      
      o_oceny = ''
      for frag in ocena[2]:
        o_oceny += '%s: %s; ' % ( t(frag[0]), t(frag[1]) )
        
      ret.append(USOS_Ocena(o_przedmiot,o_kod,o_oceny))
    return ret
    
  def wyloguj(self):
    self.mech.open('https://usosweb.uni.lodz.pl/kontroler.php?_action=actionx:logowaniecas/wyloguj()')
    if self.mech.response().read().find('Wylogowałeś się z CAS - Centralnej Usługi Uwierzytelniania.')==-1:
      raise Exception('Blad wylogowywania, na pewno byles zalogowany?')
    else:
      return True

if __name__ == '__main__':    
  try:
    baza = USOS_Baza(plik_bazy)
    usos = USOS()
    
    if not baza.ustaw_login(usos.mech):
        usos.login(login,haslo)
        baza.zapisz_login(usos.mech)

    oceny = []
    try:
      oceny = usos.pobierz_oceny()
      debug("Pobranie ocen udane")
    except Exception,e:
      if str(e[0]).count("Blad logowania")>0:
        print("Potrzebuje przelogowac..."),
        usos.login(login,haslo)
        baza.zapisz_login(usos.mech)
        oceny = usos.pobierz_oceny()
      else:
        raise

    
    for ocena in oceny:
      z_bazy = baza.pobierz(ocena)
      if z_bazy == ocena:
        continue
      elif z_bazy==None:
        baza.dodaj(ocena)
      else:
        baza.aktualizuj(ocena)
      #w razie bledow z kodowaniem albo krzaczkami, odkomentowac jedna z
      #ponizszych linijek, a zakomentowac druga:
  
      #powiadom("USOS: %s: %s" % (ocena.przedmiot,ocena.oceny))
      powiadom(("USOS: %s: %s" % (ocena.przedmiot,ocena.oceny)).encode('latin1'))
    print "OK."
    exit(0)
  except Exception,e:
    print "BLAD: %s" % e[0]
    exit(1)