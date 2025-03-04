import os
import json
import subprocess
import requests
import re
from tqdm import tqdm
from rich.console import Console
from rich.table import Table

GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes?q="
console = Console()

def display_stats(total_books, books_found, books_not_found):
    table = Table(title="📊 Statistiques de l'extraction", title_style="bold cyan")
    table.add_column("📚 Catégorie", style="bold magenta")
    table.add_column("📊 Valeur", justify="right", style="bold yellow")
    table.add_row("Nombre total de livres traités", str(total_books))
    table.add_row("✅ Livres trouvés sur Google Books", str(books_found))
    table.add_row("❌ Livres sans correspondance", str(books_not_found))
    console.print(table)
    console.print("✅ Extraction terminée. Résultats enregistrés dans [green]ebooks_not_found.json[/green].")

def clean_title(title):
    title = re.sub(r'\bT\d+\b', '', title)  # Supprime les T1, T2, etc.
    title = re.sub(r'\(.*?\)', '', title)  # Supprime les parenthèses
    return title.strip()

def get_metadata_from_ebook(epub_path):
    metadata = {"titre": None, "auteur": None, "isbn": None}
    try:
        result = subprocess.run(["ebook-meta", epub_path], capture_output=True, text=True, check=True, encoding="utf-8")
        for line in result.stdout.split("\n"):
            if line.startswith("Title"):
                metadata["titre"] = line.split(":", 1)[1].strip()
            elif line.startswith("Author"):
                metadata["auteur"] = line.split(":", 1)[1].strip()
            elif line.startswith("Identifiers"):
                match = re.search(r'isbn:(\d+)', line)
                if match:
                    metadata["isbn"] = match.group(1)
    except subprocess.CalledProcessError:
        console.print(f"❌ Erreur lors de l'extraction des métadonnées pour {epub_path}", style="bold red")
    
    if metadata["titre"]:
        metadata["titre"] = clean_title(metadata["titre"])
    return metadata if metadata["titre"] and metadata["auteur"] else None

def save_metadata_opf(metadata, folder_path):

    series = next((category for category in metadata.get("categories", []) if "tome" in category.lower() or "vol" in category.lower()), "")
    series_index = re.search(r'\b(\d+)\b', metadata.get("title", "")) 
    series_index = series_index.group(1) if series_index else ""
    rating = metadata.get("averageRating", "")

    subjects = "\n".join(
    f"            <dc:subject>{word}</dc:subject>"
    for category in metadata.get('categories', [])
    for word in category.split()
    )
    opf_content = f"""
    <?xml version='1.0' encoding='utf-8'?>
    <package xmlns="http://www.idpf.org/2007/opf" unique-identifier="uuid_id" version="2.0">
        <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
            <dc:title>{metadata['title']}</dc:title>
            <dc:creator opf:role="aut">{", ".join(metadata['authors'])}</dc:creator>
            <dc:publisher>{metadata['publisher']}</dc:publisher>
            <dc:date>{metadata['publishedDate']}</dc:date>
            <dc:description>{metadata['description']}</dc:description>
            <dc:language>{metadata['language']}</dc:language>
            <dc:identifier opf:scheme="ISBN">{next((id["identifier"] for id in metadata["industryIdentifiers"] if id["type"] == "ISBN_13"), "Unknown")}</dc:identifier>
            <dc:format>{metadata.get('printType', 'Unknown')}</dc:format>
            <dc:type>{metadata.get('printType', 'Unknown')}</dc:type>
            <dc:source>{metadata['canonicalVolumeLink']}</dc:source>
            <dc:relation>
                <opf:meta name="previewLink" content="{metadata['previewLink']}"/>
                <opf:meta name="infoLink" content="{metadata['infoLink']}"/>
            </dc:relation>
            <dc:rights>Maturity Rating: {metadata.get('maturityRating', 'Unknown')}</dc:rights>
{subjects}
            <meta name="calibre:author_link_map" content=""/>
            <meta name="calibre:series" content="{series}"/>
            <meta name="calibre:series_index" content="{series_index}"/>
            <meta name="calibre:rating" content="{rating}"/>
            <meta name="calibre:title_sort" content="{metadata['title']}"/>
            <meta name="pageCount" content="{metadata.get('pageCount', 'Unknown')}"/>
            <meta name="readingModes:text" content="{metadata['readingModes']['text']}"/>
            <meta name="readingModes:image" content="{metadata['readingModes']['image']}"/>
            <meta name="panelization:containsEpubBubbles" content="{metadata['panelizationSummary']['containsEpubBubbles']}"/>
            <meta name="panelization:containsImageBubbles" content="{metadata['panelizationSummary']['containsImageBubbles']}"/>
            {''.join(f'<dc:subject>{subject}</dc:subject>' for subject in metadata.get('categories', []))}
        </metadata>
        <manifest>
            <item id="cover" href="cover.jpg" media-type="image/jpeg"/>
        </manifest>
        <spine>
            <itemref idref="cover"/>
        </spine>
        <guide>
            <reference type="cover" title="Couverture" href="cover.jpg"/>
        </guide>
    </package>
    """.strip()

    opf_path = os.path.join(folder_path, "metadata.opf")

    with open(opf_path, "w", encoding="utf-8") as file:
        file.write(opf_content)

def download_cover_image(metadata, folder_path):
    if "imageLinks" in metadata and "thumbnail" in metadata["imageLinks"]:
        image_url = metadata["imageLinks"]["thumbnail"]
        image_path = os.path.join(folder_path, "cover.jpg")
        
        try:
            response = requests.get(image_url, stream=True, timeout=10)
            response.raise_for_status()
            
            with open(image_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
                    
        except requests.RequestException as e:
            console.print(f"❌ Erreur lors du téléchargement de la couverture : {e}", style="bold red")


def rename_book_folder(epub_path, metadata):
    folder_path = os.path.dirname(epub_path)

    clean_title = re.sub(r'[^a-zA-Z0-9]', ' ', metadata["title"])
    
    new_folder_name = " ".join(clean_title.split()).strip()

    new_folder_path = os.path.join(os.path.dirname(folder_path), new_folder_name)

    if not os.path.exists(new_folder_path):
        os.rename(folder_path, new_folder_path)
        pass

    return new_folder_path

def search_google_books(query):
    try:
        print(GOOGLE_BOOKS_API_URL + query)
        response = requests.get(GOOGLE_BOOKS_API_URL + query, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data["items"][0]["volumeInfo"] if "items" in data and data["items"] else None
    except (requests.RequestException, KeyError, IndexError):
        return None

def verify_with_google_books(metadata):
    return search_google_books(f"isbn:{metadata['isbn']}") if metadata["isbn"] else search_google_books(f"{metadata['titre']}+inauthor:{metadata['auteur']}")

def scan_epub_directory(directory):
    total_books, books_found, books_not_found = 0, 0, 0
    books_without_authors_list = []

    epub_files = [os.path.join(root, file) for root, _, files in os.walk(directory) for file in files if file.lower().endswith(".epub")]
    
    for epub_path in tqdm(epub_files, desc="📚 Traitement des EPUBs", unit="livre"):
        metadata = get_metadata_from_ebook(epub_path)
        if not metadata:
            continue
        
        google_metadata = verify_with_google_books(metadata)
        total_books += 1
        
        if google_metadata:
            books_found += 1
            folder_path = rename_book_folder(epub_path, google_metadata)
            save_metadata_opf(google_metadata, folder_path)
            download_cover_image(google_metadata, folder_path)
        else:
            books_not_found += 1
    
    with open("books_without_authors.json", "w", encoding="utf-8") as file:
        json.dump(books_without_authors_list, file, indent=4, ensure_ascii=False)

    display_stats(total_books, books_found, books_not_found)

if __name__ == "__main__":
    scan_epub_directory("./ebooks")
