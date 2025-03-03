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
    """Affiche les statistiques finales avec un joli tableau."""
    table = Table(title="📊 Statistiques de l'extraction", title_style="bold cyan")

    table.add_column("📚 Catégorie", style="bold magenta")
    table.add_column("📊 Valeur", justify="right", style="bold yellow")

    table.add_row("Nombre total de livres traités", str(total_books))
    table.add_row("✅ Livres trouvés sur Google Books", str(books_found))
    table.add_row("❌ Livres sans correspondance", str(books_not_found))

    console.print(table)
    console.print("✅ Extraction terminée. Résultats enregistrés dans [green]ebooks_not_found.json[/green].")


def clean_title(title):
    """Nettoie le titre en supprimant les indicateurs de tome (T1, T2, etc.) et les parenthèses."""
    title = re.sub(r'\bT\d+\b', '', title)  # Supprime les T1, T2, etc.
    title = re.sub(r'\(.*?\)', '', title)  # Supprime tout ce qui est entre parenthèses
    return title.strip()


def get_metadata_from_ebook(epub_path):
    """Utilise ebook-meta pour extraire le titre, l'auteur et l'ISBN du fichier EPUB."""
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


def search_google_books(query):
    """Effectue une requête Google Books avec la requête donnée et retourne les résultats."""
    response = requests.get(GOOGLE_BOOKS_API_URL + query)
    
    if response.status_code == 200:
        data = response.json()
        if "items" in data and data["items"]:
            return data["items"][0]["volumeInfo"]
    return None


def verify_with_google_books(metadata):
    """Cherche le livre sur Google Books en utilisant d'abord l'ISBN (si présent), puis le titre + auteur."""
    
    if metadata["isbn"]:
        result = search_google_books(f"isbn:{metadata['isbn']}")
        if result:
            return result 

    query = f"{metadata['titre']}+inauthor:{metadata['auteur']}".replace(" ", "+")
    return search_google_books(query)


def scan_epub_directory(directory):
    """Parcourt les dossiers et analyse les fichiers EPUB avec une barre de progression."""
    ebooks_metadata = []
    total_books = 0
    books_found = 0
    books_not_found = 0

    epub_files = [os.path.join(root, file) for root, _, files in os.walk(directory) for file in files if file.lower().endswith(".epub")]

    for epub_path in tqdm(epub_files, desc="📚 Traitement des EPUBs", unit="livre"):
        metadata = get_metadata_from_ebook(epub_path)
        if not metadata:
            continue  

        google_metadata = verify_with_google_books(metadata)

        if google_metadata:
            books_found += 1
        else:
            books_not_found += 1
            ebooks_metadata.append({
                "auteur": metadata["auteur"],
                "titre": metadata["titre"],
                "isbn": metadata["isbn"],
                "epub": epub_path
            })

        total_books += 1
        if total_books ==10:
            break

    with open("ebooks_not_found.json", "w", encoding="utf-8") as json_file:
        json.dump(ebooks_metadata, json_file, indent=4, ensure_ascii=False)

    display_stats(total_books, books_found, books_not_found)


if __name__ == "__main__":
    directory = "./ebooks" 
    scan_epub_directory(directory)
