cd

#git pull
git pull

#iniziallizzo abiente virtuale per avviare Selinium
python3 -m venv myenv

# Attiva l'ambiente virtuale
source myenv/bin/activate  # Su Mac e Linux


#analizza OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        #Cartella Su Server Linux
       echo "Server Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
       cd /Users/mohamadnaim/Documents/tvmn
       echo "Macbook"
fi



chmod +x main.py
python3 main.py

#git push
git add ./*
git commit -m 'Update Channels'
git push

#ricopio mono.m3u8 nella cartella apache
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        #ricopio
fi