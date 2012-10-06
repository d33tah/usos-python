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
