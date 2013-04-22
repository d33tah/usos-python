#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wykrywa zmiany ocen w USOS'ie i reaguje na nie.

Przykladowy plik konfiguracyjny:

def debug(str): pass
import subprocess #zeby moc uruchomic proces
login = 'PESEL'
haslo = 'HASLO'
plik_bazy = 'oceny.sqlite'
def powiadom(str):
  return subprocess.call(['/home/g/sms.orange.pl, "docelowy-nr", str, 
    "login", "haslo"])

BY Jacek Wielemborek, LICENSED UNDER CREATIVE COMMONS BY-SA LICENSE.

Kod szybkiego testowania:
from config import * ; from usos import * ; usos = USOS(); \ 
usos_baza = USOS_Baza(plik_bazy) ; usos.login(login,haslo)
"""

import sys

from USOS_Baza import USOS_Baza
from USOS import USOS
from config import plik_bazy,login,haslo,debug


if __name__ == '__main__':    

  baza = USOS_Baza(plik_bazy)
  usos = USOS()
  
  if not baza.ustaw_login(usos):
    usos.login(login,haslo)
    baza.zapisz_login(usos)
  
  oceny = []
  try:
    oceny = usos.pobierz_oceny()
    debug("Pobranie ocen udane")
  except Exception,e:
    if str(e[0]).count("Blad logowania")>0:
      print("Potrzebuje ponownie sie zalogowac..."),
      usos.login(login,haslo)
      baza.zapisz_login(usos)
      oceny = usos.pobierz_oceny()
    else:
      raise
  
  
  for ocena in oceny:
    z_bazy = baza.pobierz(ocena)
    if z_bazy == ocena:
      continue
    print ".", ; sys.stdout.flush()
    ocena.do_sredniej=usos.do_sredniej(ocena.url,ocena.typ)
    if z_bazy==None:
      baza.dodaj(ocena)
    else:
      baza.aktualizuj(ocena)
    #w razie bledow z kodowaniem, nalezy odkomentowac jedna z
    #ponizszych linijek, a zakomentowac druga:
    
    powiadom("USOS: %s: %s" % (ocena.przedmiot,ocena.oceny))
    #powiadom(("USOS: %s: %s" % (ocena.przedmiot,ocena.oceny)).encode(
    #  'latin1'))
  print "OK."
  sys.exit(0)
