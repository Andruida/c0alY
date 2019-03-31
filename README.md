# c0alYBOT

## Parancsok:

`!karomkodolista <oldal>` A legtöbbet káromkodó emberek listája

`!tortenet <member>` A megjelölt felhasználó káromkodásai

`!torol <member>` A megjelölt felhasználó káromkodási történetét és figyelmeztetéseinek számát törli

`!bug <report>` Hiba bejelentő parancs

## Testreszabási lehetőségek:

`bug_report_webhook.txt` fájlban megadható egy webhook url, amire a bot majd a bug 
report-okat discord embed formátumban küldi

`swears.txt` autómatikusan létrehozott fájl, amiben vesszővel elválasztva a szűrendő 
káromkodásokat adhatjuk meg (**Fontos:** a szavakat egy vessző és egy szóköz válassza el Pl: `szó, másikszó`)


## Szükséges discord.py változat:
```
pip install -U git+https://github.com/Rapptz/discord.py@rewrite#egg=discord.py[voice]
```
