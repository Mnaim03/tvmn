from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import os
import sys #estrazione bash
import time
import platform
import concurrent.futures #threds
from datetime import datetime #data e ora


"""
Oggetto Channel preve i seguenti attributi...
    tvgID = ID Identificativo Univoco del canale
    channelName = Nome del canale
    getM3U8 = Indica se l'M3U8 è preinserita (booleano)
    streamLink = Link streaming da sniffare
    presentM3U8 = M3U8 preiserita statica
    returnedM3U8 = M3U8 che viene utilizzita defenitivamente per l'm3u8.
                   Può essere anche un messaggio di errore o il link statico.
    category = Categoria del canale
    logo = link png dell'mmagine
"""
class Channel:
    def __init__(self, tvgID, channelName, getM3U8, streamLink, presentM3U8, category, logo):
        self.tvgID = tvgID                # key
        self.channelName = channelName    # Nome del canale
        self.getM3U8 = bool(int(getM3U8)) # Indica che l'M3U8 è preinserita (booleano)
        self.streamLink = streamLink      # Link streaming da sniffare
        self.presentM3U8 = presentM3U8    # M3U8 preiserita statica
        self.returnedM3U8 = 'none'        # M3U8 inserita dallo sniffer
        self.category = category          # Categoria del canale
        self.logo = logo                  # URL del logo del canale

    def __str__(self):
        return f"Channel({self.tvgID}, {self.getM3U8}, {self.returnedM3U8})"


"""
Passo da channels.txt a una struttura vera e propria, o anche array di Channel.
Paramentri
    filename    Nome file da cui estrarre struttura
Risultato
    channels    array di oggetti Channel
"""
def getChannelStructure(filename):
    channels = []
    channel_data = {}  # Inizializziamo `channel_data` qui

    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()  # Rimuove spazi vuoti o newline extra

            if not line:  # Salta le righe vuote
                continue

            # Dividi la riga sulla base di " = "
            if "=" in line:
                key, value = line.split("=", 1)
                channel_data[key.strip()] = value.strip()

            # Se abbiamo raccolto tutte le informazioni per un canale
            if len(channel_data) == 7:  # Ora stiamo gestendo 7 campi (senza 'returnedM3U8')
                # Fornisci un valore di default per i campi mancanti
                tvgID = channel_data.get('tvgID', 'UnknownID')
                channelName = channel_data.get('channelName', 'UnknownChannel')
                getM3U8 = channel_data.get('getM3U8', '0')  # Predefinito a '0' (falso)
                streamLink = channel_data.get('streamLink', '')
                presentM3U8 = channel_data.get('presentM3U8', '')
                category = channel_data.get('category', 'Uncategorized')
                logo = channel_data.get('logo', '')  # Predefinisci a stringa vuota se manca

                # Creiamo l'oggetto Channel e lo aggiungiamo alla lista
                channels.append(Channel(
                    tvgID=tvgID,
                    channelName=channelName,
                    getM3U8=getM3U8,
                    streamLink=streamLink,
                    presentM3U8=presentM3U8,
                    category=category,
                    logo=logo
                ))

                # Resettiamo il dizionario per il prossimo canale
                channel_data = {}  # Resettiamo `channel_data` per il prossimo canale

    return channels


"""
Conta i canali presenti in lista
Parametri
    channels    struttira da cui contora i channel
Risulato
    intero  risultato numerico del conteggio
"""
def countChannels(channels):
    var=0
    for channel in channels:
        var=var+1
    return var


"""
Data la struttura in ingresso, restitusco la struttura aggiornata con i campi returnedM3U8 e il file backup.txt
Serve anche da cordinatore del Sotto-metodi getOldM3U8, setOldM3U8, runSelinium.
Parametri
    channels    struttura da aggiornare
    backup.txt  file dei link backup da cui prendere link in caso di errore
Risultato
    channels    struttura aggiornats
    backup.txt  file dei link backup aggiornato con link più recenti
"""
def preRunSelinium(channels):
    def process_channel(channel):
        if channel.getM3U8:
            url = runSelinium(channel.streamLink)
            if url.startswith('not'):  # In caso di errore...
                channel.returnedM3U8 = getOldM3U8(channel.tvgID, url)  # Utilizzo link backup se presente
            else:
                channel.returnedM3U8 = url  # Associo il nuovo link nella struttura
                setOldM3U8(channel.tvgID, channel.returnedM3U8)  # Aggiorno link backup nella struttura
        else:
            channel.returnedM3U8 = channel.presentM3U8  # Carico il link preinserito
            setOldM3U8(channel.tvgID, channel.returnedM3U8)  # Aggiorno link backup anche se statico
        return channel

    # Usare un pool di thread con un massimo di 3 thread
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        # Mappare i canali e processarli in parallelo
        channels = list(executor.map(process_channel, channels))

    return channels


"""
permette di ottenere un link backup
Parametri
    tvgID   parametro della trutta che identifica un canale
    error   errore che si è verificato in precedenza
    backup.txt  file dei link backup da cui prendere link in caso di errore
Risultato
    return  String finale che deve essere associata a renturnedM3U8
"""
def getOldM3U8(tvgID, error):
    # Apre il file in modalità lettura
    with open("backup.txt", 'r') as file:
        # Scorre ogni linea del file
        for line in file:
            # Verifica se la linea contiene il nome della variabile richiesto
            if line.startswith(tvgID):
                # Estrae il link eliminando spazi e separando la parte dopo "="
                link = line.split('=')[1].strip()
    if link.startswith("http"):
        return link
    else:
        return "https://error.m3u8/"+error


"""
Permette di aggiornare un link backup
Parametri
    tvgID   parametro della trutta che identifica un canale
    returnedM3U8    parametro link finale
Risultato
    backup.txt  file backup aggiornato
"""
def setOldM3U8(tvgID, returnedM3U8):
    # Legge tutte le righe del file
    with open("backup.txt", 'r') as file:
        lines = file.readlines()

    # Apre il file in modalità scrittura per sovrascriverlo
    with open("backup.txt", 'w') as file:
        for line in lines:
            # Se la linea contiene il nome della variabile, modifica il link
            if line.startswith(tvgID):
                file.write(f"{tvgID}={returnedM3U8}\n")
            else:
                file.write(line)


"""
utilizzo come sotto-metodo di runSelinium() per sapere se il link interessato
coincide con quello interessato.
Parametri
    href     link m3u8 estratto da runSelinium()
Risultato
    return  ritorna un booleano che conferma o nega l'idoneetà del link m3u8
"""
def boolUrl(href):
    if (href.startswith('http://hms') or href.startswith('http://136') or href.startswith('https://el11.elahmad') or href.startswith('http://multies.xyz') or href.startswith('https://tv.ipslow.com/tv') or href.endswith('.m3u8') or href.startswith('https://playback2.akamaized')) :
        return 1
    elif (("m3u8" in href) or ("m3u" in href)):
        return 1
    else:
        return 0


"""
utilizzo Selinium su chrome per ottenere il link dal driver
Parametri
    url     link streaming
Risultato
    return  link m3u8 o messaggio di errore
"""
def runSelinium(url):

    # Imposta la variabile d'ambiente per il percorso del driver di Chrome
    if (platform.system())=='Darwin' : #in caso sia Mac
        chrome_driver_path = "chrome/chromedriver(mac)"
    else : #in caso sia Linux
        chrome_driver_path = "chrome/chromedriver(linux)"

    os.environ['PATH'] += ":" + chrome_driver_path

    # Opzioni del browser Chrome
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_extension('chrome/sniffer.crx')

    # Inizializzazione del driver di Chrome
    browser = webdriver.Chrome(options=chrome_options)
    try:
        browser.get(url)

        # Attendi il caricamento completo dell'estensione
        wait_extension = WebDriverWait(browser, 10)
        extension_loaded = wait_extension.until(EC.presence_of_element_located((By.ID, 'myM3u8LayerId')))
        wait = WebDriverWait(browser, 10)
        links = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'a')))

        for link in links:
            try:
                href = link.get_attribute('href')
                if href and ('javascript:' not in href):

                    #la condizione dell'if è il filtro dei vari link
                    if boolUrl(href): #VERIFICO CONDIZIONE
                        url=href # salva link
            except StaleElementReferenceException:
                #Elemento non più valido, continuo con il prossimo elemento
                url="not-found (Elem. Non Valido)" # salva link
                continue


    except TimeoutException:
        #Non è stato possibile caricare l'estensione o trovare l'elemento desiderato
        url = "not-found (Time-Out)"  # Restituisci "not-found" in caso di errore di timeout

    except Exception as e:
        #Errore inaspettato
        url = "not-found (Errore Inaspettato)"

    finally:
        time.sleep(6)  # Protezione anti IP-ban
        browser.quit()

    return url


"""
crea file testuale ultimi aggiornamenti
"""
def getLastUpdate(nomefile,channels):
        # Salva il vecchio stdout
        old_stdout = sys.stdout

        try:
            # Fase 1: Apri il file e reindirizza stdout al file
            with open(nomefile, 'w') as file:
                sys.stdout = file  # Reindirizza l'output standard (print) al file

                for channel in channels:
                    print(channel)

                print(f" --> {countChannels(channels)} Canali elavorati nella Struttura Channels")
                now = datetime.now()
                dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
                print(f" --> Run su {platform.system()}, alle {dt_string}")

        except Exception as e:
            # In caso di errore, stampa su stderr
            print(f"Si è verificato un errore: {e}", file=sys.stderr)

        finally:
            # Ripristina il vecchio stdout
            sys.stdout = old_stdout


"""
#scrivo il mio file .m3u8 basandomi silla classe channels
"""
def getMonoM3U8(channels, monofile):
    with open(monofile, 'w') as file:
        # Scriviamo l'intestazione del file M3U8
        file.write("#EXTM3U\n\n")

        # Per ogni canale, scriviamo il formato richiesto
        for channel in channels:
            file.write(f'#EXTINF:-4 tvg-id="{channel.tvgID}" group-title="{channel.category}" tvg-logo="{channel.logo}",{channel.channelName}\n')
            file.write(f'{channel.returnedM3U8}\n\n')  # Scriviamo il link restituito (o quello predefinito)



########
##MAIN##
########
#Carico informazioni presenti nel file channel.txt
channels =  getChannelStructure('channels.txt')

#Stampa tutti i canali caricati
for channel in channels:
    print(channel)

#ottieni lin m3u8 in caso servisse
# preRumSelinium -> runSelinium
channels = preRunSelinium(channels)


getMonoM3U8(channels,"out/mono.m3u8")

getLastUpdate("out/last-run.txt",channels)

print("----------------")
print("----- DONE -----")
print("----------------")




