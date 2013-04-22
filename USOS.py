# -*- coding: utf-8 -*- 

import mechanize
from lxml import html

from USOS_Ocena import USOS_Ocena
from config import debug

def t(obj): return obj.text_content()

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
	print "Wyjatek w mechanize.Browser().submit(), czyszcze cookies"
	print e
        self._ua_handlers['_cookies'].cookiejar = mechanize.CookieJar()
        self.open('https://logowanie.uni.lodz.pl/cas/login')
        self.select_form(nr=0)
        self.form['username']=login
        self.form['password']=haslo
        self.submit()
    
    if self.response().read().find('Udane logowanie') == -1:
      raise Exception('Blad logowania po stronie CAS.')
    
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
 
      #zapisz grupy podpiec jako string separowany srednikami.
      tmp_o_kod = ()
      for frag in ocena[1]:
        tmp_o_kod += ( t(frag) ,)
      o_kod = ' ; '.join(tmp_o_kod)
      
      o_oceny = ''
      for frag in ocena[2]:
        if len(frag)==1:
          pierwszy_termin = t(frag[0])
          typ_zajec = "(nieznany)"
        else:
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
    tree = html.fromstring(self.open(url).read())
    tabele = tree.xpath('//table [@class="grey" and '
      +'contains(.,"'+unicode(typ_zajec)+'")]')
    if len(tabele)==0:
      tabele = tree.xpath('//table [@class="grey"]')
    for tabela in tabele:
      if t(tabela.xpath('.//tr [contains (.,"Czy ocena")]/td[2]//*')[0])=='TAK':
        return True
      else:
        return False
    debug("do_sredniej(): Tu nie powinien wejsc! url=%s" % url)
