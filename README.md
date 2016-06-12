# installation 

Add the archive’s GPG key:
```
wget -q -O - https://apt.mopidy.com/mopidy.gpg | sudo apt-key add -
```
If you run Debian wheezy or Ubuntu 12.04 LTS:
```
sudo wget -q -O /etc/apt/sources.list.d/mopidy.list https://apt.mopidy.com/wheezy.list
```
Or, if you run any newer Debian/Ubuntu distro:
```
sudo wget -q -O /etc/apt/sources.list.d/mopidy.list https://apt.mopidy.com/jessie.list
```
Install pyspotify and all dependencies:
```
sudo apt-get update
sudo apt-get install python-spotify

sudo apt-get install libspotify-dev

sudo apt-get install build-essential python-dev python3-dev libffi-dev

sudo apt-get install libasound2-dev
```
add your .key file to your application directory.

```
pip install -e .
```
### settings 

create your settings.ini
```
cp settings.ini.dist settings.ini
```
### run
```
python -m spotifypiclient.client
```