import pandas as pd
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, tostring
import re
import os # Importar os para verificar la existencia del archivo

# --- Configuración de Archivos ---
# El nombre del archivo CSV de origen.
INPUT_CSV_FILENAME = "Tesis de Pregrado - Ingeniería Agrícola.csv" # Ajusta esta ruta si es necesario en tu máquina local

# El nombre del archivo de salida en formato XML.
OUTPUT_XML_FILENAME = "referencias_agricola.xml" # Puedes cambiar el nombre si lo deseas

# --- Definición del Mapeo de Campos ---
# Mapea las columnas del CSV a la ruta de los elementos XML según Zayas.xml.
csv_to_xml_mapping = {
    'dc.contributor.author[]': 'contributors/authors/author',
    'dc.contributor.author': 'contributors/authors/author',
    'dc.title[en_US]': 'titles/title',
    'dc.title': 'titles/title',
    'dc.date.issued[]': 'dates/year',
    'dc.date.issued': 'dates/year',
    'dc.publisher[en_US]': 'publisher',
    'dc.publisher': 'publisher',
    'dc.description.abstract[en_US]': 'abstract',
    'dc.description.abstract': 'abstract',
    'dc.subject[en_US]': 'keywords/keyword',
    'dc.subject.other[en_US]': 'keywords/keyword',
    'dc.identifier.uri[]': 'urls/web-urls/url',
    'dc.identifier.uri': 'urls/web-urls/url',
    'dc.language.iso[en_US]': 'language'
}

def clean_author(author_string: str) -> str:
    """Limpia el campo de autor para mantener solo el nombre."""
    if pd.isna(author_string):
        return ""
    # Elimina los UUIDs de DSpace que siguen al nombre (ej: "Apellido, Nombre::uuid::600")
    # También elimina los nombres de las instituciones si están presentes (ej: "Apellido, Nombre (Institución)::uuid::600")
    cleaned = re.sub(r'\s*\(.*?\)\s*::[a-f0-9-]+::\d+$', '', author_string) # Elimina (Institución)::uuid::digitos
    cleaned = re.sub(r'::[a-f0-9-]+::\d+$', '', cleaned).strip() # Elimina solo ::uuid::digitos si no hay (Institución)
    return cleaned

def clean_and_format_value(value, xml_tag):
    """Limpieza y formateo de valores específicos según la etiqueta XML."""
    if pd.isna(value):
        return ""
    value_str = str(value).strip()

    # Limpieza general: reemplazar saltos de línea y comillas dobles residuales
    value_str = value_str.replace('\r\n', ' ').replace('\n', ' ').replace('"', '')

    if xml_tag == 'dates/year':
        # Extraer solo el año (asume formato "YYYY-MM-DDTHH:MM:SSZ" o similar)
        match = re.search(r'^\d{4}', value_str)
        return match.group(0) if match else ""

    elif xml_tag == 'keywords/keyword':
        # Las palabras clave a veces vienen separadas por || o ;. Devolvemos una lista.
        return [k.strip() for k in re.split(r'[\|]{2,}|;', value_str) if k.strip()]

    elif xml_tag == 'contributors/authors/author':
        # Limpieza especial para autores
        return clean_author(value_str)

    else:
        return value_str

def main():
    """Función principal para leer el CSV, convertir a XML y escribir el archivo."""
    if not os.path.exists(INPUT_CSV_FILENAME):
        print(f"Error: El archivo '{INPUT_CSV_FILENAME}' no se encontró.")
        print("Asegúrate de que el archivo CSV esté en el mismo directorio que el script o ajusta la ruta.")
        return

    try:
        # Leer el archivo CSV en un DataFrame de pandas
        df = pd.read_csv(INPUT_CSV_FILENAME)
        print(f"Archivo CSV '{INPUT_CSV_FILENAME}' cargado exitosamente.")

    except Exception as e:
        print(f"Ocurrió un error al leer el archivo CSV: {e}")
        return

    # Crear el elemento raíz <xml>
    root = Element('xml')
    records = SubElement(root, 'records')

    # Iterar sobre cada fila del DataFrame y crear elementos XML
    for index, row in df.iterrows():
        record = SubElement(records, 'record')

        # Añadir elementos fijos según Zayas.xml
        SubElement(record, 'database', name='MyLibrary').text = 'MyLibrary'
        SubElement(record, 'source-app', name='Zotero').text = 'Zotero'
        # Asumimos que todos son Tesis (ref-type 32)
        SubElement(record, 'ref-type', name='Thesis').text = '32'

        # Procesar los campos según el mapeo
        for csv_col, xml_path in csv_to_xml_mapping.items():
            if csv_col in row and not pd.isna(row[csv_col]):
                value = row[csv_col]
                cleaned_value = clean_and_format_value(value, xml_path)

                if cleaned_value:
                    # Manejar casos con múltiples valores (como palabras clave)
                    if isinstance(cleaned_value, list):
                        path_parts = xml_path.split('/')
                        current_element = record
                        for part in path_parts[:-1]:
                            found_element = current_element.find(part)
                            if found_element is None:
                                current_element = SubElement(current_element, part)
                            else:
                                current_element = found_element
                        for item in cleaned_value:
                            SubElement(current_element, path_parts[-1]).text = item
                    else:
                        # Crear elementos para valores únicos
                        path_parts = xml_path.split('/')
                        current_element = record
                        for part in path_parts[:-1]:
                             found_element = current_element.find(part)
                             if found_element is None:
                                 current_element = SubElement(current_element, part)
                             else:
                                 current_element = found_element
                        SubElement(current_element, path_parts[-1]).text = cleaned_value

    try:
        # Escribir la estructura XML a un archivo con formato legible
        from xml.dom import minidom

        xml_string = tostring(root, encoding='utf-8')
        pretty_xml_string = minidom.parseString(xml_string).toprettyxml(indent="  ")

        with open(OUTPUT_XML_FILENAME, "w", encoding="utf-8") as f:
            f.write(pretty_xml_string)

        print(f"\n¡Conversión a XML completa!")
        print(f"El archivo de referencias '{OUTPUT_XML_FILENAME}' ha sido creado.")

    except Exception as e:
        print(f"Ocurrió un error al escribir el archivo XML: {e}")

if __name__ == "__main__":
    main()
