#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pobiera od uzytkownika login oraz haslo do USOSa i podaje mu
srednia ocen z podzialem na kierunki i semestry.

Przykladowy config:

def debug(str): pass
import subprocess #zeby moc uruchomic proces
login = 'PESEL'
haslo = 'HASLO'
plik_bazy = 'oceny.sqlite'
def powiadom(str):
  return subprocess.call(['/home/g/sms.orange.pl, "docelowy-nr", str, 
    "login", "haslo"])

BY d33tah, LICENSED UNDER CREATIVE COMMONS BY-SA LICENSE.
"""

import sys
from getpass import getpass

from USOS_Baza import USOS_Baza
from USOS import USOS


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
	    print ".", ; sys.stdout.flush()
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
