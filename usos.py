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

bpython pastie:
from config import * ; from usos import * ; usos = USOS(); \ 
usos_baza = USOS_Baza(plik_bazy) ; usos.login(login,haslo)
"""

import pickle
import sys

try:
  import sqlite3
except ImportError:
  import pysqlite2.dbapi2 as sqlite3
import mechanize
from lxml import html

from config import *

from getpass import getpass

def t(obj): return obj.text_content()
def debug(str): pass
#def debug(str): print str
#def powiadom(str): print str
#def powiadom(str): pass

class USOS_Baza:
  
  
  def __init__(self,plik_bazy):
    self.conn = sqlite3.connect(plik_bazy)
    self.c = self.conn.cursor()
    self.c.execute("CREATE TABLE IF NOT EXISTS oceny " +
        "(przedmiot TEXT, \
          kod TEXT, \
          typ TEXT, \
          do_sredniej TEXT, \
          url TEXT, \
          ocena TEXT)")
    self.c.execute("CREATE TABLE IF NOT EXISTS config " +
        "(klucz TEXT UNIQUE, \
          tresc BLOB)")
    self.conn.commit()

    
  def pobierz(self,ocena):
    debug("Pobieram %s" % ocena.przedmiot)
    ret = self.c.execute("SELECT * FROM oceny WHERE \
      przedmiot = ? \
      AND typ = ? \
      AND url = ? \
      AND kod = ?",(ocena.przedmiot,ocena.typ,ocena.url,ocena.kod) ).fetchone()
    if ret:
      return USOS_Ocena(ret[0],ret[1],ret[2], ret[3]=="True", ret[4], ret[5])
  
  def dodaj(self,ocena):
    debug("Dodaje %s" % ocena.przedmiot)
    self.c.execute("INSERT INTO oceny VALUES (?,?,?,?,?,?)",
      (ocena.przedmiot,
       ocena.kod,
       ocena.typ,
       ocena.do_sredniej,
       ocena.url,
       ocena.oceny) )
    self.conn.commit()

  def aktualizuj(self,ocena):
    debug("Updatuje %s" % ocena.przedmiot)
    self.c.execute("UPDATE oceny SET ocena = ? WHERE \
      przedmiot = ? \
      AND kod = ? \
      AND typ = ? \
      AND do_sredniej = ? \
      AND url = ?",
      (ocena.oceny,
       ocena.przedmiot,
       ocena.kod, 
       ocena.typ, 
       ocena.do_sredniej, 
       ocena.url))
    self.conn.commit()

  def ustaw_login(self,mech):
    debug("Pobieram login...");
    ret = self.c.execute("SELECT * FROM config WHERE klucz = ?", 
      ("cookies", )).fetchone()

    if ret:
      mech._ua_handlers['_cookies'].cookiejar = pickle.loads(str(ret[1]))
      return True
    else:
      return False

  def zapisz_login(self,mech):
    debug("Zapisuje login...");
    tresc = pickle.dumps(mech._ua_handlers['_cookies'].cookiejar)
    ret = self.c.execute("SELECT * FROM config WHERE klucz = ?", 
      ("cookies", )).fetchone()
    if ret:
      debug("Juz cos jest.")
      self.c.execute("UPDATE config SET tresc = ? WHERE klucz = ?", 
        (tresc, "cookies")).fetchone()
      self.conn.commit()
      return True
    else:
      debug("Jeszcze nic nie ma...")
      self.c.execute("INSERT INTO config VALUES (?,?)" , ("cookies", tresc))
      self.conn.commit()
      return True

class USOS_Ocena:
  
  
  def __init__(self,przedmiot,kod,typ,do_sredniej,url,oceny):
    self.przedmiot = przedmiot
    self.kod = kod
    self.typ = typ
    self.do_sredniej = do_sredniej
    self.url = url
    self.oceny = oceny
    
  def __eq__(obj1,obj2):
    if isinstance(obj1,USOS_Ocena) and isinstance(obj2,USOS_Ocena):
      return ((obj1.przedmiot,obj1.kod,obj1.typ,obj1.url,obj1.oceny)==
              (obj2.przedmiot,obj2.kod,obj2.typ,obj2.url,obj2.oceny)
         and (obj1.do_sredniej=="-1" or obj2.do_sredniej=="-1" or 
         obj1.do_sredniej==obj2.do_sredniej))
                  
  def __str__(self):
    return "<USOS_Ocena: przedmiot='%s' kod='%s' typ='%s' do_sredniej='%s' \
url='%s' oceny='%s'>" % (self.przedmiot,self.kod,self.typ,self.do_sredniej,
self.oceny)


class USOS(mechanize.Browser):
    
  
  def __init__(self):
    
    mechanize.Browser.__init__(self)
    self.set_handle_robots(False)
    #user_agent = 'Mozilla/4.0 (compatible; MSIE 6.0; ' + \
    #'Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)'
    #self.addheaders += [("User-agent",user_agent)]
    self.addheaders += [("Accept-Language",
                                      'pl-PL,pl;q=0.8,en-US;q=0.6,en;q=0.4')]
    
  def login(self,login,haslo):

    try:    
        self.open('https://logowanie.uni.lodz.pl/cas/login')
        self.select_form(nr=0)
        self.form['username']=login
        self.form['password']=haslo
        self.submit()
    except Exception,e:
        self._ua_handlers['_cookies'].cookiejar = mechanize.CookieJar()
        self.open('https://logowanie.uni.lodz.pl/cas/login')
        self.select_form(nr=0)
        self.form['username']=login
        self.form['password']=haslo
        self.submit()
    
    if self.response().read().find('Udane logowanie') == -1:
      raise Exception('Blad logowania po stronie CAS.')
    
    #w sumie nie wiem po co to tu, ale bez tego zapytania nie dziala :P
    self.open('https://usosweb.uni.lodz.pl/kontroler.php?'+
                              '_action=actionx:logowaniecas/index()')
    
  def pobierz_oceny(self):
  
    ret = []
  
    self.open('https://usosweb.uni.lodz.pl/kontroler.php?'+
                              '_action=actionx:dla_stud/studia/oceny/index()')
    response = self.response().read()
    if response.find("Zalogowany: <b") == -1:
      raise Exception('Blad logowania po stronie USOS.')
    
    tree = html.fromstring(response)
    for ocena in tree.xpath('//table [@class = "grey"]//tr'):

      
      if len(ocena) != 4:
        continue
      if t(ocena[2][0]) == '(brak ocen)':
        continue
      
      o_przedmiot = t(ocena[0][0])
 
      #zapisz grupy podpiec jako string separowany srednikami. pewnie ladniej by
      #bylo wyrazeniami lambda albo jednolinikowym forem, ale nie chcialo mi sie
      #kombinowac.
      tmp_o_kod = ()
      for frag in ocena[1]:
        tmp_o_kod += ( t(frag) ,)
      o_kod = ' ; '.join(tmp_o_kod)
      
      o_oceny = ''
      for frag in ocena[2]:
        typ_zajec = t(frag[0])
        pierwszy_termin = t(frag[1])
        do_sredniej = "-1"
        url_do_sredniej=ocena[3].find('.//a').get('href')
        #do_sredniej = self.do_sredniej(url,typ_zajec)
        if len(frag)!=3:
          ret.append(USOS_Ocena(o_przedmiot,o_kod, typ_zajec,do_sredniej,
            url_do_sredniej,pierwszy_termin ))
        else:
          drugi_termin = t(frag[2])
          ret.append(USOS_Ocena(o_przedmiot,o_kod, typ_zajec,do_sredniej,
            url_do_sredniej,pierwszy_termin+' '+drugi_termin))

    return ret
    
  def wyloguj(self):
    self.open('https://usosweb.uni.lodz.pl/kontroler.php?_action='+
      'actionx:logowaniecas/wyloguj()')
    if self.response().read().find('Wylogowałeś się z CAS - Centralnej Usługi'+
        ' Uwierzytelniania.')==-1:
      raise Exception('Blad wylogowywania, na pewno byles zalogowany?')
    else:
      return True

  def do_sredniej(self,url,typ_zajec):
    print ".", ; sys.stdout.flush()
    tree = html.fromstring(self.open(url).read())
    tabele = tree.xpath('//table [@class="grey" and '
      +'contains(.,"'+unicode(typ_zajec)+'")]')
    for tabela in tabele:
      if t(tabela.xpath('.//tr [contains (.,"Czy ocena")]/td[2]//*')[0])=='TAK':
        return True
      else:
        return False
    debug("do_sredniej(): Tu nie powinien wejsc! url=%s" % url)

def policz_srednia():
    usos = USOS()
    t_login = getpass('PESEL: ')
    t_haslo = getpass('Haslo: ')
    usos.login(t_login,t_haslo)
    oceny = usos.pobierz_oceny()

    #uporzadkuj oceny wedlug slownika 'kody'
    kody = {}
    for ocena in oceny:
      tmp_kody = ocena.kod.split(' ')
      if len(tmp_kody)!=2:
        debug("tmp_kody!=2 - %s" % ocena.przedmiot)
        break
      kierunek=tmp_kody[0]
      semestr = tmp_kody[1].replace('('+tmp_kody[0], '').rstrip(')')
      if not semestr:
        semestr='?'
      elif semestr.find(')')!=-1:
        semestr = semestr.rsplit(')',1)[1]
      if not kierunek in kody:
        kody[kierunek] = {}
      if not semestr in kody[kierunek]:
         kody[kierunek][semestr] = []
      kody[kierunek][semestr].append(ocena)

    wszystkie_liczba=0.0
    wszystkie_suma=0
    for kierunek in kody:
      kierunek_liczba=0.0
      kierunek_suma=0
      print "Kierunek %s" % kierunek
      semestry = kody[kierunek].keys()
      semestry.sort()
      for semestr in semestry:
        print "->Semestr %s -" % semestr, 
        liczba = 0.0
        suma = 0
        for przedmiot in kody[kierunek][semestr]:
          if przedmiot.oceny=="ZWL":
            continue
          if przedmiot.do_sredniej=="-1":
            przedmiot.do_sredniej=usos.do_sredniej(przedmiot.url,przedmiot.typ)
          if przedmiot.oceny.startswith('('):
            if przedmiot.do_sredniej:
              liczba+=1
              suma+=float(przedmiot.oceny.split(') ')[0].replace(
                ',','.').strip('('))+float(przedmiot.oceny.split(
                ') ')[1].replace(',','.'))/2
              #suma+=float(przedmiot.oceny.split(') ')[1].replace(',','.'))
          else:
            if przedmiot.do_sredniej:
              liczba+=1
              suma+=float(przedmiot.oceny.replace(',','.'))
        if liczba!=0:
          print "średnia: %f" % (float(suma)/liczba),
        print " "
        kierunek_liczba+=liczba
        wszystkie_liczba+=kierunek_liczba
        kierunek_suma+=suma
        wszystkie_suma+=kierunek_suma
      if kierunek_liczba!=0:
        print "Średnia dla kierunku: %s\n" % (
          float(kierunek_suma)/kierunek_liczba)
    print "Średnia ogólna: %s" % (float(wszystkie_suma)/wszystkie_liczba)

if __name__ == '__main__':    
  policz_srednia()
  sys.exit(0)

  baza = USOS_Baza(plik_bazy)
  usos = USOS()
  
  if not baza.ustaw_login(usos):
    #usos.login(login,haslo)
    #baza.zapisz_login(usos)

  oceny = []
  try:
    oceny = usos.pobierz_oceny()
    debug("Pobranie ocen udane")
  except Exception,e:
    if str(e[0]).count("Blad logowania")>0:
      print("Potrzebuje przelogowac..."),
      usos.login(login,haslo)
      baza.zapisz_login(usos)
      oceny = usos.pobierz_oceny()
    else:
      raise

  
  for ocena in oceny:
    z_bazy = baza.pobierz(ocena)
    if z_bazy == ocena:
      continue
    ocena.do_sredniej=usos.do_sredniej(ocena.url,ocena.typ)
    if z_bazy==None:
      baza.dodaj(ocena)
    else:
      baza.aktualizuj(ocena)
    #w razie bledow z kodowaniem albo krzaczkami, odkomentowac jedna z
    #ponizszych linijek, a zakomentowac druga:

    powiadom("USOS: %s: %s" % (ocena.przedmiot,ocena.oceny))
    #powiadom(("USOS: %s: %s" % (ocena.przedmiot,ocena.oceny)).encode(
    #  'latin1'))
  print "OK."
  sys.exit(0)
