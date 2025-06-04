import json
import os
from ebooklib import epub
import uuid


def generate_epub_from_json(json_file, output_file):
    """Generate an EPUB file from the processed JSON content."""

    # Read the JSON file
    with open(json_file, 'r') as f:
        book_data = json.load(f)

    # Create a new EPUB book
    book = epub.EpubBook()

    # Set metadata
    title = None
    author = None
    cover_image = None

    # Extract title, author, and cover from the JSON data
    for item in book_data:
        if item['type'] == 'title':
            title = item['content']
        elif item['type'] == 'author':
            author = item['content']
        elif item['type'] == 'cover' and 'image' in item:
            cover_image = item['image']
        if title and author and cover_image:
            break

    if not title:
        raise ValueError("ebook is missing section 'title'")
    if not author:
        raise ValueError("ebook is missing section 'author'")
    if not cover_image:
        raise ValueError("ebook is missing section 'cover_image'")

    bookdID = str(uuid.uuid4())
    print(f"Set id {bookdID}")
    book.set_identifier(bookdID)
    print(f"Set title {title}")
    book.set_title(title)
    print(f"Set language 'en'")
    book.set_language('en')
    print(f"Set author {author}")
    book.add_author(author)

    cover_path = os.path.join(os.path.dirname(json_file), cover_image)
    if not os.path.exists(cover_path):
        raise ValueError(f"cover image {cover_path} not found")

    # Read the cover image
    with open(cover_path, 'rb') as f:
        cover_content = f.read()

    # Add the cover image to the book
    print(f"Set cover {cover_path}")
    book.set_cover("cover.png", cover_content)

    # Process content into chapters
    chapters = []
    current_chapter_content = []
    current_chapter_title = "Cover"
    chapter_counter = 0
    division_counter = 0
    image_counter = 1

    # Create a list to keep track of all images for reference
    all_images = []

    for item in book_data:
        if item['type'] == 'chapter_header':
            # If we have content for a previous chapter, save it
            if current_chapter_content:
                if division_counter > 1:
                    chapter = epub.EpubHtml(
                        title=f"{current_chapter_title} - {chapter_counter}.{division_counter}",
                        file_name=f'chapter_{chapter_counter}.xhtml'
                    )
                else:
                    chapter = epub.EpubHtml(
                        title=current_chapter_title,
                        file_name=f'chapter_{chapter_counter}.xhtml'
                    )
                chapter.content = ''.join(current_chapter_content)
                chapters.append(chapter)
                chapter_counter += 1
                current_chapter_content = []

            current_chapter_title = f"Chapter {item['content']}"
            current_chapter_content.append(f"<h1>{item['content']}</h1>")
            division_counter = 1
        elif item['type'] in 'title':
            current_chapter_content.append(f"<h1>{item['content']}</h1>")
        elif item['type'] in 'author':
            current_chapter_content.append(f"<h2>{item['content']}</h2>")
        elif item['type'] in ('cover','image') and 'image' in item:
            # Add image to the content
            img_path = os.path.join(os.path.dirname(json_file), item['image'])
            if os.path.exists(img_path):
                img_filename = f"image_{image_counter}.png"
                image_counter += 1

                # Read the image
                with open(img_path, 'rb') as f:
                    img_content = f.read()

                # Create image item
                img_item = epub.EpubItem(
                    uid=f"image_{len(all_images) + 1}",
                    file_name=f"images/{img_filename}",
                    media_type="image/png",
                    content=img_content
                )
                book.add_item(img_item)
                all_images.append(img_item)

                # Add image reference to the chapter content
                caption = item.get('caption', '')
                if caption:
                    current_chapter_content.append(
                        f'<div class="image-container"><img src="images/{img_filename}" alt="{caption}"/><p class="caption">{caption}</p></div>'
                    )
                else:
                    current_chapter_content.append(
                        f'<div class="image-container"><img src="images/{img_filename}" alt="Image"/></div>'
                    )
        else:
            # Build HTML content based on the type
            if item['type'] == 'paragraph':
                current_chapter_content.append(f"<p>{item['content']}</p>")
            elif item['type'] == 'bold':
                current_chapter_content.append(f"<p><strong>{item['content']}</strong></p>")
            elif item['type'] == 'block_indent':
                current_chapter_content.append(f"<blockquote>{item['content']}</blockquote>")
            elif item['type'] == 'sub_header':
                current_chapter_content.append(f"<h3>{item['content']}</h3>")
            elif item['type'] == 'header':
                current_chapter_content.append(f"<h2>{item['content']}</h2>")
            elif item['type'] == 'page_division':
                # If we have content for a previous chapter, save it
                if current_chapter_content:
                    if division_counter > 1:
                        chapter = epub.EpubHtml(
                            title=f"{current_chapter_title} - {chapter_counter}.{division_counter}",
                            file_name=f'chapter_{chapter_counter}.{division_counter}.xhtml'
                        )
                    else:
                        chapter = epub.EpubHtml(
                            title=current_chapter_title,
                            file_name=f'chapter_{chapter_counter}.{division_counter}.xhtml'
                        )
                    chapter.content = ''.join(current_chapter_content)
                    chapters.append(chapter)
                    current_chapter_content = []

                division_counter += 1
                current_chapter_content.append("<hr/>")

    # Add the last chapter if there's content
    if current_chapter_content:
        if division_counter > 1:
            chapter = epub.EpubHtml(
                title=f"{current_chapter_title} - {chapter_counter}.{division_counter}",
                file_name=f'chapter_{chapter_counter}.xhtml'
            )
        else:
            chapter = epub.EpubHtml(
                title=current_chapter_title,
                file_name=f'chapter_{chapter_counter}.xhtml'
            )
        chapter.content = ''.join(current_chapter_content)
        chapters.append(chapter)

    # Add chapters to the book
    for chapter in chapters:
        print(f"Added chapter {chapter.title}")
        book.add_item(chapter)

    # Define TOC
    book.toc = [(epub.Section('Chapters'), chapters)]

    # Add default NCX and Nav files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Define CSS style
    style = '''
    @namespace epub "http://www.idpf.org/2007/ops";
    body {
        font-family: Cambria, Liberation Serif, Bitstream Vera Serif, Georgia, Times, Times New Roman, serif;
        margin: 5%;
        text-align: justify;
    }
    h1, h2, h3 {
        text-align: center;
        margin-bottom: 1em;
    }
    blockquote {
        margin: 1em 2em;
        font-style: italic;
    }
    .image-container {
        text-align: center;
        margin: 1em 0;
    }
    .image-container img {
        max-width: 100%;
        height: auto;
    }
    .caption {
        font-style: italic;
        font-size: 0.9em;
        margin-top: 0.5em;
    }
    '''

    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=style
    )
    book.add_item(nav_css)

    # Create spine
    book.spine = ['nav'] + chapters

    # Write the EPUB file
    epub.write_epub(output_file, book, {})
    return output_file


if __name__ == "__main__":
    directory = "out"
    book_json = os.path.join(directory, "book.json")
    output_epub = os.path.join(directory, "book.epub")
    generate_epub_from_json(book_json, output_epub)
    print(f"EPUB file created: {output_epub}")