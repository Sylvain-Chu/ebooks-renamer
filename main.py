import os
import json
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
        
        isbn = None
        for identifier in identifiers:
            if 'isbn' in identifier.text.lower() or identifier.get('opf:scheme') == 'ISBN':
                isbn = identifier.text
                break
        
        return {
            'title': title.text if title is not None else None,
            'author': author.text if author is not None else None,
            'date': date.text if date is not None else None,
            'publisher': publisher.text if publisher is not None else None,
            'isbn': isbn,
            'language': language.text if language is not None else None,
            'description': description.text if description is not None else None,
            'subjects': [subject.text for subject in subjects]
        }
    except ET.ParseError:
        print(f"Erreur de parsing du fichier : {opf_path}")
        return None

def parcours_ebook(directory):
    book_count = 0
    folder_without_opf = 0
    ebooks_metadata = []

    for root, dirs, files in os.walk(directory):
        opf_found = False
        for file in files:
            if file.endswith(".opf"):
                opf_found = True
                opf_path = os.path.join(root, file)
                metadata = extract_metadata_from_opf(opf_path)
                if metadata:
                    book_count += 1
                    ebooks_metadata.append(metadata)
                    print(f"Fichier OPF : {opf_path}")
                    print(f"Titre : {metadata['title']}")
                    print(f"Auteur : {metadata['author']}")
                    print(f"Date : {metadata['date']}")
                    print(f"Éditeur : {metadata['publisher']}")
                    print(f"ISBN : {metadata['isbn']}")
                    print(f"Langue : {metadata['language']}")
                    print(f"Description : {metadata['description'][:200] if metadata['description'] else 'Aucune description disponible'}...")
                    print(f"Sujets : {metadata['subjects']}")
                    print("-" * 50)
        if not opf_found:
            folder_without_opf += 1
    
    print(f"Total books found: {book_count}")
    print(f"Folders without OPF file: {folder_without_opf}")
    
    with open("ebooks_metadata.json", "w", encoding="utf-8") as json_file:
        json.dump(ebooks_metadata, json_file, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    ebooks_directory = "./ebooks"
    parcours_ebook(ebooks_directory)

