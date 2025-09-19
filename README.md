# 🥋 UFC Web Scraper

Proyecto de web scraping a la página de la UFC (https://www.ufc.com), diseñado con el objetivo de automatizar la recolección de datos relevante de sus eventos, las peleas y sus peleadores, para luego poder utilizarlos en análisis posteriores o integrarlos en otras aplicaciones.
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
  - Peleadores por cada esquina
  - Estadísticas de la pelea por esquina
  - Ganador
  - Información de finalización (Ganador, método de victoria, round y tiempo de finalización)
- Peleadores:
  - Información biográfica (Nombre, apodo, lugar de nacimiento, edad)
  - Medidas (Altura, Peso, Alcance)
  - Estilo de pelea
  - Información profesional (Record profesional, categoría de peso, fecha de debut en UFC)
  - Estadísticas de pelea (Golpes dados por posición y por objetivo, Derribos logrados e intentados)

## 🛠️ Requisitos

Este proyecto está desarrollado en **Python 3.12.11** y utiliza las siguientes librerías principales:
- pandas
- requests
- beautifulsoup4

Puedes instalarlas ejecutando:

```bash
pip install -r requirements.txt
```

## 🚀 Uso

Para ejecutar el scraper, abre el notebook principal:

```bash
jupyter notebook ufc_webscraper.ipynb
```

En el notebook encontrarás:
- Configuración de parámetros necesarios para las peticiones
- Funciones necesarias para la recolección de datos
- Información de los datasets ya transformados a DataFrames

## 📈 Resultados

La ejecución del scraper genera tres datasets estructurados en formato CSV:
- Eventos
- Peleas
- Peleadores

Estos archivos constituyen la base de datos para futuros análisis y modelados.

## 🚧 Futuro trabajo

- Análisis exploratorio de los datos de los datasets  
- Modelado de algoritmo de machine learning de clasificación para determinar ganadores en futuras peleas  

## 📄 Licencia

Este proyecto está bajo la licencia **MIT**. Ver archivo [LICENSE](LICENSE) para más detalles.
