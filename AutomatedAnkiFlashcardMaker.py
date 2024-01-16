from PIL import Image
import fitz  
import os
import requests



pdf_directory = "pdf_files_directory"  # Specify the directory containing your PDF files
pdf_files = [file for file in os.listdir(pdf_directory) if file.endswith(".pdf")]
anki_base_url = "http://localhost:8765"  # AnkiConnect API base URL
output_question_dir = "path_to_existing_questions_folder"  # Directory for question screenshots
output_answer_dir = "path_to_existing_answers_folder"  # Directory for answer screenshots



def clear_directory_contents(directory_path):
    # Clear the contents of a directory by deleting all files inside it
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")



def extract_questions_and_answers(pdf_path):
    questions = []
    answers = []
    doc = fitz.open(pdf_path)

    current_question = ""
    is_question_page = True  # Start with the assumption that the first page contains questions

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text().lower()

        if "mark scheme" in text:
            is_question_page = False  # Switch to answers after "mark scheme"

        if is_question_page:
            if text.startswith("question"):
                if current_question:
                    questions.append(current_question.strip())
                current_question = text
            else:
                current_question += "\n" + text
        else:
            answers.append(text)

    if current_question:
        questions.append(current_question.strip())

    return questions, answers






def capture_and_save_region_as_image(page, region_text, output_dir, image_name_prefix, index):
    rect = page.searchFor(region_text)
    if rect:
        left, top, right, bottom = rect[0]
        region_image = page.get_pixmap(x0=left, y0=top, x1=right, y1=bottom)

        # Save the region image
        region_image.save(os.path.join(output_dir, f"{image_name_prefix}_{index}.png"))

def take_question_and_answer_screenshots(pdf_path, output_question_dir, output_answer_dir):
    questions, answers = extract_questions_and_answers(pdf_path)
    doc = fitz.open(pdf_path)

    for i, (q_page_num, question_text) in enumerate(questions, start=1):
        # Capture and save the question region as an image
        q_page_num, question_text = questions[i - 1]
        page = doc[q_page_num - 1]
        capture_and_save_region_as_image(page, question_text, output_question_dir, "question", i)

        # Capture and save the answer region as an image
        a_page_num, answer_text = answers[i - 1]
        page = doc[a_page_num - 1]
        capture_and_save_region_as_image(page, answer_text, output_answer_dir, "answer", i)






def create_anki_deck(deck_name):
    # Create a new Anki deck using AnkiConnect
    anki_create_deck_url = f"{anki_base_url}/createDeck"
    deck_data = {"deck": deck_name}
    response = requests.post(anki_create_deck_url, json=deck_data)



def add_anki_card(deck_name, question_image_path, answer_image_path):
    # Add a new Anki card to the specified deck using AnkiConnect
    anki_add_card_url = f"{anki_base_url}/addNote"
    card_data = {
        "note": {
            "deckName": deck_name,
            "modelName": "Basic",
            "fields": {
                "Front": f"<img src='{question_image_path}'/>",  # Embed question image
                "Back": f"<img src='{answer_image_path}'/>"  # Embed answer image
            }
        }
    }
    response = requests.post(anki_add_card_url, json=card_data)



def process_pdf_and_create_anki_deck(pdf_path, pdf_file):
    # Clear the contents of the question and answer directories
    clear_directory_contents(output_question_dir)
    clear_directory_contents(output_answer_dir)

    # Process the PDF and take screenshots, saving images
    take_question_and_answer_screenshots(pdf_path, output_question_dir, output_answer_dir)

    # Create a separate Anki deck for this PDF
    deck_name = pdf_file.replace(".pdf", "")
    create_anki_deck(deck_name)

    question_image_files = os.listdir(output_question_dir)

    for i in range(1, len(question_image_files) + 1):
        question_image_file = os.path.join(output_question_dir, f"question_{i}.png")
        answer_image_file = os.path.join(output_answer_dir, f"answer_{i}.png")
        add_anki_card(deck_name, question_image_file, answer_image_file)



# Iterate through PDF files in the directory and process each one
for pdf_file in pdf_files:
    pdf_path = os.path.join(pdf_directory, pdf_file)
    process_pdf_and_create_anki_deck(pdf_path, pdf_file)
