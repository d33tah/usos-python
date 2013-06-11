#!/bin/bash
cd #pracujemy w katalogu domowym

#ustawiamy prywatna konfiguracje pythona. utworzy katalogi ~/bin, ~/lib i ~/include
	wget http://peak.telecommunity.com/dist/virtual-python.py
	python virtual-python.py
	rm virtual-python.py

#dzieki temu programy z ~/bin beda mialy pierwszenstwo przed pozostalymi
        if [ "$SHELL" = "/bin/zsh" ]; then
                PROFILE=~/.zshrc
        fi

        if [ "$SHELL" = "/bin/bash" ]; then
                PROFILE=~/.bashrc
        fi

        if ! grep -q 'PATH=$HOME/bin:$PATH' $PROFILE; then
                sed -i '1i \\n#DODANE AUTOMATYCZNIE PRZEZ usos-python:\nPATH=$HOME/bin:$PATH\n' $PROFILE
                export PATH=$PATH:$HOME/bin
        fi;
#teraz zainstalujemy nasza wersje easy_install, ktora nie bedzie wymagac uprawnien administratora
	wget 'http://pypi.python.org/packages/source/s/setuptools/setuptools-0.6c11.tar.gz'
	tar xvf setuptools-0.6c11.tar.gz setuptools-0.6c11/ez_setup.py
	python setuptools-0.6c11/ez_setup.py

	rm setuptools-0.6c11/ez_setup.py
	rmdir setuptools-0.6c11
	rm setuptools-0.6c11.tar.gz
	rm setuptools-0.6c11-py2.5.egg

#instalujemy potrzebne biblioteki
	easy_install mechanize
	easy_install lxml

#pobieramy najnowszego usos-pythona
	git clone git://github.com/d33tah/usos-python.git

#konfigurujemy go... (na razie dziala tylko pod plusem; konieczna rejestracja na simplus.pl)

	#wybieramy i instalujemy bramke SMS
	echo >&2
        echo ">wybierz bramke SMS (eraapiprv, eraomnix, miastoplusa, orange, playmobile): " >&2
        select sms_bin in eraapiprv eraomnix miastoplusa orange playmobile
        do
                case "$sms_bin" in
                        eraapiprv|eraomnix|miastoplusa|orange|playmobile) break;;
                esac
        done
	wget "http://skrypty-sms.googlecode.com/svn/trunk/sms.${sms_bin}.pl" -O ~/usos-python/sms
	chmod +x ~/usos-python/sms
	
	echo > ~/usos-python/config.py
	echo 'def debug(str): pass' >> ~/usos-python/config.py
	echo >> ~/usos-python/config.py

	echo '#zamienia znak ~ na sciezke do katalogu domowego' >> ~/usos-python/config.py
	echo 'from os.path import expanduser' >> ~/usos-python/config.py
	echo 'import subprocess #potrzebne do wykonywania polecen' >> ~/usos-python/config.py

	echo >&2
	echo "Najpierw zapytam o dane do USOS'a (nie wyswietli sie)." >&2
	trap "stty echo; exit" INT TERM EXIT #jesli skrypt sie przerwie, odblokuj terminal
	read -s -p ">login: " usos_login
	echo "login='${usos_login}'" >> ~/usos-python/config.py
        read -s -p ">haslo: " usos_password
        echo "haslo='${usos_password}'" >> ~/usos-python/config.py

	echo "plik_bazy = expanduser('~/usos-python/oceny.sqlite')" >> ~/usos-python/config.py
	echo >> ~/usos-python/config.py

	#pierwsze uruchomienie, nie chcemy jeszcze zeby wyslal sms
	echo "Nastapi proba zalogowania (moze potrwac kilka minut)" >&2
	echo >> ~/usos-python/config.py
	echo "def powiadom(str): print str #pozniej mozna usunac ta linijke" >> ~/usos-python/config.py
	echo >> ~/usos-python/config.py
	~/bin/python ~/usos-python/usos.py
	
	echo >&2
	echo "Teraz zapytam o dane do bramki SMS. (ukryje tylko haslo)" >&2
	read -p ">twoj nr tel: " sms_tel
	read -p ">twoj login: " sms_login
	read -s -p ">twoje haslo: " sms_password

	echo "def powiadom(str):" >> ~/usos-python/config.py
	echo "  return subprocess.call([expanduser('~/usos-python/sms'), '${sms_tel}', str, " >> ~/usos-python/config.py
	echo "  '${sms_login}', '${sms_password}'])" >> ~/usos-python/config.py

#uruchamiamy nasz program:
	screen -S usos-python -d -m sh -c $' 
	( while true; do echo -n '`date`: '; ~/bin/python ~/usos-python/usos.py; sleep 600; done ) | tee -a ~/usos-python/log.txt '

#i to na tyle. aby przejrzec jego logi/wylaczyc go, wykonujemy 'screen -X -S usos-python quit'
	echo "Gotowe. usos-python uruchomiony. Aby go wylaczyc, wykonaj 'screen -X -S usos-python quit'."
