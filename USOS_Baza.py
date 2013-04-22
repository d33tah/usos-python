import pickle

try:
  import sqlite3
except ImportError:
  import pysqlite2.dbapi2 as sqlite3

from config import debug

from USOS_Ocena import USOS_Ocena

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
    debug("Aktualizuje %s" % ocena.przedmiot)
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
