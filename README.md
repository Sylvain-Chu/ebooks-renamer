# Ebook Metadata Extractor

## Description
This script scans a directory containing ebooks and extracts metadata from OPF (Open Packaging Format) files. It displays the following information for each detected ebook:

- **Title**
- **Author**
- **Publication Date**
- **Publisher**
- **ISBN**
- **Language**
- **Description (truncated to 200 characters if available)**
- **Associated Subjects**

At the end of execution, it also displays:
- The total number of detected books
- The number of folders without an OPF file

## Prerequisites
- Python 3

## Installation
No special installation is required. Just ensure that Python 3 is installed on your system.

## Usage
1. Place your ebooks in a directory structured as follows:

```
./ebooks/
    ├── author1/
    │   ├── book1/
    │   │   ├── metadata.opf
    │   │   ├── book1.epub
    │   │   ├── cover.jpg
    │   │   └── ...
    ├── author2/
    │   ├── book2/
    │   │   ├── metadata.opf
    │   │   ├── book2.epub
    │   │   ├── cover.jpg
    │   │   └── ...
    ├── author_without_opf/
    │   ├── book_without_opf/
    │   │   ├── book_without_opf.epub
    │   │   ├── cover.jpg
    │   │   └── ...
```

2. Run the script with the following command:

```sh
python main.py
```

## Ebook Structure
The script expects an organization where each ebook is contained in a separate folder, with an `.opf` file containing the metadata. If a folder does not contain an `.opf` file, it will be counted as a "folder without an OPF file."

## Results
On each execution, the script displays the metadata of detected ebooks and provides a summary of the total number of books and folders without OPF metadata.

## Evolution
A future improvement involves fetching additional metadata using an external API based on the ISBN number. This will help verify and correct metadata inaccuracies from the OPF file, ensuring the extracted information is as precise as possible.
