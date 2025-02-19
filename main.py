import os
import xml.etree.ElementTree as ET

def extract_metadata_from_opf(opf_path):
    try:
        namespaces = {
            'dc': 'http://purl.org/dc/elements/1.1/',
            'opf': 'http://www.idpf.org/2007/opf'
        }

        tree = ET.parse(opf_path)
        root = tree.getroot()

        title = root.find('.//dc:title', namespaces)
        author = root.find('.//dc:creator', namespaces)
        date = root.find('.//dc:date', namespaces)
        publisher = root.find('.//dc:publisher', namespaces)
        identifiers = root.findall('.//dc:identifier', namespaces)
        language = root.find('.//dc:language', namespaces)
        description = root.find('.//dc:description', namespaces)
        subjects = root.findall('.//dc:subject', namespaces)

        return {
            'title': title.text if title is not None else "Titre inconnu",
            'author': author.text if author is not None else "Auteur inconnu",
            'date': date.text if date is not None else "Date inconnue",
            'publisher': publisher.text if publisher is not None else "Editeur inconnu",
            'identifiers': {id.get('id'): id.text for id in identifiers if id.get('id')},
            'language': language.text if language is not None else "Langue inconnue",
            'description': description.text if description is not None else "Pas de description",
            'subjects': [subject.text for subject in subjects if subject.text]
        }
    
    except ET.ParseError:
        return None

def parcours_ebook(directory):
    book_count = 0
    empty_folders = 0

    for root, dirs, files in os.walk(directory):
        opf_files = [file for file in files if file.endswith(".opf")]

        if not opf_files:
            empty_folders += 1
            continue

        for file in opf_files:
            opf_path = os.path.join(root, file)
            metadata = extract_metadata_from_opf(opf_path)
            if metadata:
                book_count += 1
                print(f"Fichier OPF : {opf_path}")
                print(f"Titre : {metadata['title']}")
                print(f"Auteur : {metadata['author']}")
                print(f"Date : {metadata['date']}")
                print(f"Editeur : {metadata['publisher']}")
                print(f"Identifiants : {', '.join(metadata['identifiers']) if metadata['identifiers'] else 'Aucun'}")
                print(f"Langue : {metadata['language']}")
                description = metadata['description']
                if description and description != "Pas de description":
                    print(f"Description : {description[:200]}...")
                else:
                    print("Description : Aucune description disponible")
                print(f"Sujets : {', '.join(metadata['subjects']) if metadata['subjects'] else 'Aucun'}")
                print("-" * 50)  

    print(f"\nNombre total de livres trouvés : {book_count}")
    print(f"Nombre de dossiers sans fichier OPF : {empty_folders}")

if __name__ == "__main__":
    ebooks_directory = "./ebooks"
    parcours_ebook(ebooks_directory)
