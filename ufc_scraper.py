# Standard Library
import os
import time
from pathlib import Path

# Third-party Libraries
import pandas as pd
import requests
from bs4 import BeautifulSoup


# Requests
def safe_request(url, timeout, **kwargs):
    try:
        response = requests.get(url, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response

    except requests.RequestException:
        return None


# HTML helpers
def get_html(data):
    for item in data:
        if item.get('command') == 'insert' and item.get('data'):
            return item.get('data')
    return None


def get_tags(soup, keys, div, label_class, value_class):

    LABEL_MAP = {
        "place_of_birth": "place_of_birth",
        "ciudad_natal": "place_of_birth",
        "fighting_style": "fighting_style",
        "estilo_de_lucha": "fighting_style",
        "age": "age",
        "años": "age",
        "height": "height",
        "alto": "height",
        "weight": "weight",
        "peso": "weight",
        "octagon_debut": "octagon_debut",
        "debut_del_octágono": "octagon_debut",
        "reach": "reach",
        "alcance": "reach",
        "leg_reach": "leg_reach",
        "alcance_de_la_pierna": "leg_reach",
        "ko/tko": "ko/tko",
        "dec": "dec",
        "sub": "sub"
    }

    data = {key: None for key in keys}

    values = soup.find_all(class_=div)

    for value in values:

        raw_label = value.find(class_=label_class)
        raw_value = value.find(class_=value_class)

        if not raw_label or not raw_value:
            continue

        label_text = raw_label.text.strip().lower()
        label_text = label_text.replace(".", "").replace(" ", "_")

        label_tag = LABEL_MAP.get(label_text)

        value_text = raw_value.text.split("(")[0].strip()

        try:
            if value_text == "":
                value_tag = None
            elif "." in value_text:
                value_tag = float(value_text)
            else:
                value_tag = int(value_text)
        except ValueError:
            value_tag = value_text

        if label_tag in data:
            data[label_tag] = value_tag

    return data


def data_filler(soup, class_):
    tag = soup.find(class_=class_)
    return tag.text.strip() if tag else None


# Output
def dynamic_print(context, total=None, old=None, element=''):
    os.system("cls" if os.name == 'nt' else 'clear')

    if context == 'progress':
        print(f"Registrados {total} {element}")

    elif context == 'updating':
        if total is None or old is None:
            print(f"Archivos actualizados, nuevos {element} registrados")
        else:
            print(
                f"Archivos actualizados, {total - old} nuevos {element} registrados")

    elif context == 'loading':
        print("Datos cargados correctamente")


# Filesystem
def make_dir(dir_):
    data_dir = Path(dir_.get("data_dir", "data"))
    data_dir.mkdir(parents=True, exist_ok=True)

    return {
        key: data_dir / file
        for key, file in dir_.get('files', {}).items()
    }


# Scraper helpers
def update_dynamic_cols(hrefs, headers):
    data = []

    for href in hrefs:

        response = safe_request(
            "https://www.ufc.com" + href, (5, 10), headers=headers)
        if response is None:
            continue
        soup = BeautifulSoup(response.content, 'html.parser')

        bio = get_tags(soup, ['age', 'status'],
                       "c-bio__field", "c-bio__label", "c-bio__text")

        data.append({
            'href': href,
            'age': bio['age'],
            'is_active': bio['status']
        })

        time.sleep(1)

    return pd.DataFrame(data)


# Scraper de peleadores
def get_profile(url, href, headers):

    # Descargar y analizar el código HTML de la página
    response = safe_request(url + href, (5, 10), headers=headers)
    if response is None:
        return None
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extraer biografía y estadísticas del peleador
    method = get_tags(soup, ['ko/tko', 'dec', 'sub'],
                      "c-stat-3bar__group", "c-stat-3bar__label", "c-stat-3bar__value") or {}
    bio = get_tags(soup, ['place_of_birth', 'fighting_style', 'age', 'height', 'weight',
                   'octagon_debut', 'reach', 'leg_reach'], "c-bio__field", "c-bio__label", "c-bio__text") or {}

    # Completar información del peleador
    profile = {
        'href': href,
        'name': data_filler(soup, "hero-profile__name"),  # Biografía
        'nickname': data_filler(soup, "hero-profile__nickname"),
        'place_of_birth': bio.get('place_of_birth'),
        'age': bio.get('age'),
        'height': bio.get('height'),  # Medidas
        'reach': bio.get('reach'),
        'leg_reach': bio.get('leg_reach'),
        # Información de carrera
        'fighting_style': bio.get('fighting_style'),
        'ufc_debut_date': bio.get('octagon_debut'),
        'professional_record': data_filler(soup, "hero-profile__division-body"),
        'ko_tko_wins': method.get('ko/tko'),
        'decision_wins': method.get('dec'),
        'submission_wins': method.get('sub'),
        # Estado de actividad}
        'is_active': any(tag.get_text(strip=True).lower() in ('active', 'activo')
                         for tag in soup.find_all(class_="hero-profile__tag"))
    }
    return profile


def get_fighters(config, saved_fighters):
    fighters_list = []

    while True:
        # Descargar y convertir la respuesta JSON de la página
        response = safe_request(config['url'],
                                (5, 10),
                                headers=config['headers'],
                                params=config['fighters']['params'])
        if response is None:
            print("Error de conexión. Se detiene el scraping de peleadores.")
            return pd.DataFrame(fighters_list)
        data = response.json()

        # Extraer contenido HTML
        html = get_html(data)
        if not html:
            break

        # Analizar  HTML y obtener enlaces
        soup = BeautifulSoup(html, 'html.parser')
        href_in_page = soup.find_all('a', class_='e-button--black')
        if not href_in_page:
            break

        # Obtener y guardar perfil de los peleadores
        for a_tag in href_in_page:
            href = (a_tag.get('href') or '').strip()
            if not href or href in saved_fighters:
                continue
            saved_fighters.add(href)
            fighter = get_profile(
                'https://www.ufc.com', href, config['headers'])
            if fighter is not None:
                fighters_list.append(fighter)

        # Imprimir estado del progreso de la ejecución
        dynamic_print('progress', total=len(
            fighters_list), element='peleadores')

        config['fighters']['params']['page'] += 1
        time.sleep(1)

    return pd.DataFrame(fighters_list)


def fighters_scraper(config):
    paths = make_dir(config['fighters']['dir'])
    fighters_path = paths['fighters']

    # Si existe el archivo, lo actualizo
    if fighters_path.exists():
        print("Actualizando archivos...")

        # Cargar los peleadores existentes y aislar sus identificadores únicos
        old_fighters = pd.read_csv(fighters_path)
        saved_fighters = set(old_fighters['href'])

        # Actualizar datos
        new_fighters = get_fighters(config, saved_fighters)

        # Concatenar nuevos peleadores a los existentes
        fighters = pd.concat([new_fighters, old_fighters],
                             ignore_index=True).drop_duplicates()

        # Obtener nuevos valores de columnas dinámicas
        dynamic_cols = update_dynamic_cols(fighters['href'], config['headers'])

        # Ordenar DataFrames por 'href' como identificador único
        fighters = fighters.merge(
            dynamic_cols, on='href', how='left', suffixes=("", "_new"))

        # Reemplazar datos y eliminar columnas auxiliares
        fighters['age'] = fighters['age_new']
        fighters['is_active'] = fighters['is_active_new']
        fighters = fighters.drop(columns=['age_new', 'is_active_new'])

        # Guardar DataFrame actualizado
        fighters.to_csv(fighters_path, index=False)

        dynamic_print('updating', total=len(fighters),
                      old=len(old_fighters), element='peleadores')

    # Si no, crearlos desde cero
    else:
        print("Cargando datos...")

        # Bajar datos
        saved_fighters = set()
        fighters = get_fighters(config, saved_fighters)

        # Crear archivos
        fighters.to_csv(fighters_path, index=False)

        dynamic_print('loading')


# Scraper de eventos
def get_event(url, href, headers):

    # Descargar y analizar el código HTML de la página
    response = safe_request(url + href, (5, 10), headers=headers)
    if response is None:
        return None
    soup = BeautifulSoup(response.content, 'html.parser')

    # Buscar las IDs de cada pelea
    tags = soup.find_all('div', class_='c-listing-fight')

    if not tags:
        return None

    tag_id = tags[0].get('data-fmid')
    if not tag_id:
        return None

    # Definir url para la petición de la pelea
    event_url = f"https://d29dxerjsp82wz.cloudfront.net/api/v3/fight/live/{tag_id}.json"

    # Obtener información de la pelea
    response = safe_request(event_url, (5, 10), headers=headers)
    if response is None:
        return None
    data = response.json()

    data = data.get('LiveFightDetail', {})

    # Completar informción de la pelea
    event_data = data.get('Event', {})
    location = event_data.get('Location', {})
    event = {
        'href': href,
        'name': event_data.get('Name'),
        'date': event_data.get('StartTime'),
        'country': location.get('Country'),
        'city': location.get('City'),
        'venue': location.get('Venue')
    }

    return event


def get_fight(id_, headers):

    def get_outcome(data, winner=True):

        for fighter in data:
            outcome = fighter.get('Outcome', {}).get('Outcome', {})

            if outcome != 'Loss':
                if outcome == 'Win' and winner:

                    name = fighter.get('Name', {})
                    first = name.get('FirstName', {})
                    last = name.get('LastName', {})

                    return f"{first} {last}".strip()

                elif outcome in ('Draw', 'No Contest') and not winner:
                    return outcome
        return None

    # Definir url para la petición de cada pelea
    fights_url = f"https://d29dxerjsp82wz.cloudfront.net/api/v3/fight/live/{id_}.json"

    # Obtener información de la pelea
    response = safe_request(fights_url, (5, 10), headers=headers)
    if response is None:
        return None
    data = response.json()

    data = data.get('LiveFightDetail', {})

    # Separar información
    weight_class = data.get('WeightClass', {})
    result = data.get('Result', {})
    corner_info = data.get('Fighters', [])
    corner_stats = data.get('FightStats', [])

    if len(corner_info) == 2:
        red_data, blue_data = corner_info[0], corner_info[1]
    else:
        red_data, blue_data = {}, {}
    if len(corner_stats) == 2:
        red_stats, blue_stats = corner_stats[0], corner_stats[1]
    else:
        red_stats, blue_stats = {}, {}

    # Completar informción de la pelea
    fight = {
        'fight_id': id_,
        'event': data.get('Event', {}).get('Name', None),
        # Fight info
        'weight_class': None if weight_class.get('CatchWeight') else weight_class.get('Description', None),
        'weight': weight_class.get('Weight', None),
        'catch_weight_lbs': weight_class.get('CatchWeight', None),
        'accolades': (data.get('Accolades', [{}])[0].get('Type', 'Regular') if data.get('Accolades') else 'Regular'),
        'possible_rounds': data.get('RuleSet', {}).get('PossibleRounds', None),
        'card_segment': data.get('CardSegment', None),
        'fight_order': data.get('FightOrder', None),
        'status': data.get('Status', None),
        'winner': get_outcome(data.get('Fighters', [])),
        'outcome': get_outcome(data.get('Fighters', []), winner=False),
        'round': result.get('EndingRound', None),
        'time': result.get('EndingTime', None),
        'method': result.get('Method', None),
        'ending_submission': result.get('EndingSubmission', None),
        'fight_of_the_night': result.get('FightOfTheNight', None),
        'referee': f"{data.get('Referee', {}).get('FirstName', '')} {data.get('Referee', {}).get('LastName', '')}".strip(),
        # Red Corner info
        'red_corner': f"{red_data.get('Name', {}).get('FirstName', '')} {red_data.get('Name', {}).get('LastName', '')}".strip(),
        'total_strikes_attempted_red': red_stats.get('TotalStrikesAttempted', None),
        'total_strikes_landed_red': red_stats.get('TotalStrikesLanded', None),
        'significant_strikes_attempted_red': red_stats.get('SigStrikesAttempted', None),
        'significant_strikes_landed_red': red_stats.get('SigStrikesLanded', None),
        'knockdowns_red': red_stats.get('Knockdowns', None),
        # By Target
        'head_significant_strikes_red': red_stats.get('SigHeadStrikesLanded', None),
        'body_significant_strikes_red': red_stats.get('SigBodyStrikesLanded', None),
        'leg_significant_strikes_red': red_stats.get('SigLegStrikesLanded', None),
        # By Position
        'distance_significant_strikes_red': red_stats.get('SigDistanceStrikesLanded', None),
        'clinch_significant_strikes_red': red_stats.get('SigClinchStrikesLanded', None),
        'ground_significant_strikes_red': red_stats.get('SigGroundStrikesLanded', None),
        # Takedowns
        'takedowns_attempted_red': red_stats.get('TakedownsAttempted', None),
        'takedowns_landed_red': red_stats.get('TakedownsLanded', None),
        'submission_attempts_red': red_stats.get('SubmissionsAttempted', None),
        'reversals_red': red_stats.get('Reversals', None),  # Control
        'clinch_control_time_red': red_stats.get('ClinchControlTime', None),
        'ground_control_time_red': red_stats.get('GroundControlTime', None),
        'ko_of_the_night_red': red_data.get('KOOfTheNight', None),  # Awards
        'submission_of_the_night_red': red_data.get('SubmissionOfTheNight', None),
        'performance_of_the_night_red': red_data.get('PerformanceOfTheNight', None),
        # Blue Corner info
        'blue_corner': f"{blue_data.get('Name', {}).get('FirstName', '')} {blue_data.get('Name', {}).get('LastName', '')}".strip(),
        'total_strikes_attempted_blue': blue_stats.get('TotalStrikesAttempted', None),
        'total_strikes_landed_blue': blue_stats.get('TotalStrikesLanded', None),
        'significant_strikes_attempted_blue': blue_stats.get('SigStrikesAttempted', None),
        'significant_strikes_landed_blue': blue_stats.get('SigStrikesLanded', None),
        'knockdowns_blue': blue_stats.get('Knockdowns', None),
        # By Target
        'head_significant_strikes_blue': blue_stats.get('SigHeadStrikesLanded', None),
        'body_significant_strikes_blue': blue_stats.get('SigBodyStrikesLanded', None),
        'leg_significant_strikes_blue': blue_stats.get('SigLegStrikesLanded', None),
        # By Position
        'distance_significant_strikes_blue': blue_stats.get('SigDistanceStrikesLanded', None),
        'clinch_significant_strikes_blue': blue_stats.get('SigClinchStrikesLanded', None),
        'ground_significant_strikes_blue': blue_stats.get('SigGroundStrikesLanded', None),
        # Takedowns
        'takedowns_attempted_blue': blue_stats.get('TakedownsAttempted', None),
        'takedowns_landed_blue': blue_stats.get('TakedownsLanded', None),
        'submission_attempts_blue': blue_stats.get('SubmissionsAttempted', None),
        'reversals_blue': blue_stats.get('Reversals', None),  # control
        'clinch_control_time_blue': blue_stats.get('ClinchControlTime', None),
        'ground_control_time_blue': blue_stats.get('GroundControlTime', None),
        'ko_of_the_night_blue': blue_data.get('KOOfTheNight', None),  # Awards
        'submission_of_the_night_blue': blue_data.get('SubmissionOfTheNight', None),
        'performance_of_the_night_blue': blue_data.get('PerformanceOfTheNight', None)
    }

    return fight


def get_fights(url, href, headers):

    fights_list = []

    # Descargar y analizar el código HTML de la página
    response = safe_request(url + href, (5, 10), headers=headers)
    if response is None:
        return []
    soup = BeautifulSoup(response.content, 'html.parser')

    # Buscar las IDs de cada pelea
    tags = soup.find_all('div', class_='c-listing-fight')

    if not tags:
        return []

    for tag in tags:

        tag_id = tag.get('data-fmid')
        if not tag_id:
            continue

        fight = get_fight(tag_id, headers)
        if fight is not None:
            fights_list.append(fight)

    return fights_list


def get_events(config, saved_events):
    fights_list = []
    events_list = []

    while True:

        # Descargar y convertir la respuesta JSON de la página
        response = safe_request(config['url'],
                                (5, 10),
                                headers=config['headers'],
                                params=config['events']['params'])
        if response is None:
            print("Error de conexión. Se detiene el scraping de eventos")
            return pd.DataFrame(fights_list), pd.DataFrame(events_list)
        data = response.json()

        # Extraer contenido HTML
        html = get_html(data)
        if not html:
            break

        # Analizar  HTML y obtener enlaces
        soup = BeautifulSoup(html, 'html.parser')
        href_in_page = soup.select('h3.c-card-event--result__headline a')
        if not href_in_page:
            break

        # Obtener y guardar información de peleas y eventos
        for a_tag in href_in_page:
            href = (a_tag.get('href') or '').strip()
            if not href or href in saved_events:
                continue
            saved_events.add(href)
            fights = get_fights(
                "https://www.ufc.com", href, config['headers'])
            event = get_event("https://www.ufc.com", href, config['headers'])
            if fights is not None:
                fights_list.extend(fights)
            if event is not None:
                events_list.append(event)

        # Imprimir estado del progreso de la ejecución
        dynamic_print('progress', total=len(events_list), element='eventos')

        config['events']['params']['page'] += 1
        time.sleep(1)

    return pd.DataFrame(fights_list), pd.DataFrame(events_list)


def events_scraper(config):
    paths = make_dir(config['events']['dir'])
    fights_path = paths['fights']
    events_path = paths['events']

    # Si existen los dos datasets, los actualizo
    if fights_path.exists() and events_path.exists():
        print("Actualizando archivos...")

        # Cargo los datos existentes, y aíslo sus identificadores únicos
        old_fights = pd.read_csv(fights_path)
        old_events = pd.read_csv(events_path)
        saved_events = set(old_events['href'])

        # Actualizar datos
        new_fights, new_events = get_events(config, saved_events)

        # fights
        fights = pd.concat([new_fights, old_fights],
                           ignore_index=True).drop_duplicates()
        fights.to_csv(fights_path, index=False)

        # Events
        events = pd.concat([new_events, old_events],
                           ignore_index=True).drop_duplicates()
        events.to_csv(events_path, index=False)

        dynamic_print('updating', total=len(events),
                      old=len(old_events), element='eventos')

    # Si no, los creo de cero
    else:
        print("Cargando datos...")

        # Bajar datos
        saved_events = set()
        fights, events = get_events(config, saved_events)

        # Crear archivos
        fights.to_csv(fights_path, index=False)
        events.to_csv(events_path, index=False)

        dynamic_print('loading')


def main():

    CONFIG = {
        'url': 'https://www.ufc.com/views/ajax',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 OPR/120.0.0.0',
            'Referer': 'https://www.ufc.com/',
            'Origin': 'https://www.ufc.com',
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br, zstd'
        },
        'fighters': {
            'params': {
                'view_name': 'all_athletes',
                'view_display_id': 'page',
                'view_args': '',
                'view_path': '/athletes/all',
                'view_base_path': '',
                'view_dom_id': '2c3c312fe4dc9787715f2863a8c5a6fa87f2e1be4cf3c18799fea36d0b19d864',
                'pager_element': 0,
                'page': 0,
                'ajax_page_state[theme]': 'ufc',
                'ajax_page_state[theme_token]': '',
                'ajax_page_state[libraries]': 'eJx1UkGOwyAM_FAIT0IOOIlbgiPstE1fvwSodg9bCaGZwRjbA4SgDOm00ME4Z046TODvTrms3f7B7iZfjxRf5R6qYnb42lkwuJlioWLhKEFyTBt9DVkwYYY4hAfaBwXkYQaPKjbkY4c4NjZGSnfzpLCg_h_wIHyKgRu8hggnH-oCiecH5tNyQs9x2DnGz60LmyupDHKK4lZ6EhyO2dvpUOUkFbcqjWBEr1VZIk8QjRf5S2-N1YQmZN4DP1OXRCktBnSNqO2FDdNhNqAWscPSZCntT5DNTFm0K4pmZi41_PIVIXT-xEkzpiCGd6WN3jWRgyA2lxlPkFKLdH1mgpD9Wgapa-n-sqUe0rLqDlINWznTG5S4Vucie4hdKEmXj94y2V84Qoyud1mn4c7yM_qLpZQ8VIts3ceNwxGxSe5yzRVn7Qd0ndJMqbTsxOfLu-bxRzVN_QFZ8BWy'
            },
            'dir': {
                'data_dir': 'data',
                'files': {
                    'fighters': 'ufc_fighters.csv'
                }
            },
        },
        'events': {
            'params': {
                'view_name': 'events_upcoming_past',
                'view_display_id': 'past',
                'view_args': '',
                'view_path': '/events',
                'view_base_path': '',
                'view_dom_id': '2e422ed07970c73b149fbe6e6a2a328005c2f81634d5e5add883f14b4dab4ab4',
                'pager_element': 0,
                'page': 0,
                'ajax_page_state[theme]': 'ufc',
                'ajax_page_state[theme_token]': '',
                'ajax_page_state[libraries]': 'eJx1kQGOhCAMRS8kcpG9A6lQlBmkhhYd9_TLgGYn2WxC4P_XpC0tOCcE6dRwidFnSjJMYJ9GqJ5Nf2jz4H9Dgi8Z3I56Dw5p8AGjM3OmsmmMuGKScaEcvmt6iEZg4iHCSUWMC2xpx3xqSmgpDhvFqF0uG8TxrVUM6ckDnyy41qKMQ_FWT0WEEjdtITuFe61yWyqMsRkfomBW1aLt4TnSBFFZ5k_76G7BTF3QoYTUAWKXj9x_sWrfbMGQFFgJlJprfSuXaXN0dFQHUdQKobsN5v4XrkObICsfMstFBJUnqq3_-gXBXb5NsAoDjnVGZyZIqcdM64p1f75Cz2h8mBfZgFlDkbYLuDs1kSzEC9Rs883PulXNCNkutUAe9oAH63aPK7kSsSMDD3iZGUXf4uIh-ZBq64Ztfq-1UXVT1ekPOsf5fw'
            },
            'dir': {
                'data_dir': 'data',
                'files': {
                    'fights': 'ufc_fights.csv',
                    'events': 'ufc_events.csv'
                }
            }
        }
    }

    fighters_scraper(CONFIG)
    events_scraper(CONFIG)


if __name__ == "__main__":
    main()
