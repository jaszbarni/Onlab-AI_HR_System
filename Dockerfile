# 1. Használjunk egy hivatalos, könnyű (slim) Python alapképet
FROM python:3.11-slim

# 2. Ne generáljunk .pyc fájlokat, és az output egyből jelenjen meg a konzolon
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Munkakönyvtár beállítása a konténeren belül
WORKDIR /app

# 4. CSAK a requirements.txt másolása elsőként
# Ez egy trükk: a Docker ezt a réteget gyorsítótárazza (cache), így ha csak a kódod 
# változik, nem kell újra letölteni az összes csomagot minden buildnél!
COPY requirements.txt .

# 5. Függőségek telepítése
RUN pip install --no-cache-dir -r requirements.txt

# 6. A maradék kód (a projekted) átmásolása a munkakönyvtárba
COPY . .

# 7. (Opcionális) Ha a programod egy szerver, nyisd meg a portot
EXPOSE 8501

# 8. A parancs, ami elindítja a programodat
CMD ["python", "main.py"]