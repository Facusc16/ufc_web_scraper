# 🥋 UFC Web Scraper

Proyecto de web scraping a la página de la UFC (https://www.ufc.com), diseñado con el objetivo de automatizar la recolección de datos relevantes de sus eventos, las peleas y sus peleadores, para luego poder utilizarlos en análisis posteriores o integrarlos en otras aplicaciones.
Los datasets recolectados se almacenan en archivos CSV para facilitar su posterior exploración y análisis con herramientas de análisis de datos.

## 📊 Datasets

De la ejecución del código resultan 3 datasets distintos con la siguiente informacion principal:

- Eventos:
  - Nombre
  - Fecha
  - Localización
- Peleas:
  - Nombre del evento
  - Categoría de peso
  - Nombre del Referee
  - Peleadores por esquina
  - Estadísticas de la pelea por esquina
  - Ganador
  - Información de finalización (Ganador, método de victoria, round y tiempo de finalización)
- Peleadores:
  - Información biográfica (Nombre, apodo, lugar de nacimiento, edad)
  - Medidas (Altura, Peso, Alcance)
  - Estilo de pelea
  - Información profesional (Record profesional, categoría de peso, fecha de debut en UFC)
  - Cantidad de finalizaciones (KO/TKO, sumisión, decisión)

## 🛠️ Requisitos

Este proyecto está desarrollado en **Python 3.12.1** y utiliza las siguientes librerías principales:

- pandas
- requests
- beautifulsoup4

Puedes instalarlas ejecutando:

```bash
pip install -r requirements.txt
```

## 🚀 Uso

Para su uso, ejecute el script .py:

```bash
jupyter ufc_scraper.py
```

En el notebook encontrarás:

- Configuración de parámetros necesarios para las peticiones
- Funciones necesarias para la recolección de datos

## 📈 Resultados

La ejecución del scraper genera tres datasets estructurados en formato CSV:

- Eventos
- Peleas
- Peleadores

Estos archivos constituyen la base de datos para futuros análisis y modelados.

## 🚧 Futuros trabajos

- Análisis exploratorio de los datos de los datasets
- Modelado de algoritmo de machine learning de clasificación para determinar ganadores en futuras peleas

## 📄 Licencia

Este proyecto está bajo la licencia **MIT**. Ver archivo [LICENSE](LICENSE) para más detalles.
