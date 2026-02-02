from sys import exit
from os import path, listdir, environ

import fitz
import aspose.pdf as ap

from tempfile import TemporaryDirectory

import csv
import pandas as pd
from inference.providers.deepinfra import DeepInfraClient
import Levenshtein
from langchain_text_splitters import MarkdownHeaderTextSplitter



#TODO: parsing works, good enough for now but could need some refinement on out of text image placements


#### pdf ####
#due to aspose limitations
def chunk_pdf(pdf_path, out_dir_path, chunk_page_count=4):
    with fitz.open(pdf_path) as doc:
        for start_page in range(0, doc.page_count, chunk_page_count):
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=start_page, to_page= min(start_page + chunk_page_count, doc.page_count) - 1)
            new_doc.save(path.join(out_dir_path, f"{path.basename(pdf_path).replace(".pdf", "")}_chunk{start_page+1}_{start_page + chunk_page_count - 1}.pdf"))
            new_doc.close()



def align_intext_images(text_parts, images, inline_threshold=4, only_in_text=True):
    output = []

    while images:
        to_match = images.pop(0)

        n_previous_elements =  next((i for i, x in enumerate(text_parts) if x["center"].y > to_match["center"].y - inline_threshold), 1) - 1
        n_previous_elements = 0 if n_previous_elements < 0 else n_previous_elements
        output += text_parts[:n_previous_elements]
        text_parts = text_parts[n_previous_elements:]
        
        row_elements = list(filter(lambda x: abs(to_match["center"].y - x["center"].y) <= inline_threshold, text_parts))
        matched = next(iter(sorted(row_elements, key=lambda x: abs(ap.Point.distance(to_match["center"], x["center"])))), None)
        
        if matched:
            m_index = text_parts.index(matched)
            output += text_parts[:m_index]
            output.append(to_match)
            text_parts = text_parts[m_index:]

        elif not only_in_text:
            output.append(to_match)     

    output += text_parts


    return output
        


def parse_pagecontents(pdf_path):
    output = {}

    text_parser = ap.text.TextFragmentAbsorber()
    image_parser = ap.ImagePlacementAbsorber()
    doc = ap.Document(pdf_path)
    doc.pages.accept(text_parser)
    doc.pages.accept(image_parser)
    text_fragments = text_parser.text_fragments
    images = image_parser.image_placements
    

    for text in text_fragments:
        page_num = text.page.number
        center = text.rectangle.center()
        content = text.text 

        output.setdefault(page_num, {"text": [], "images": []})
        output[page_num]["text"].append({"center": center, "content": content})

    for img in images:
        page_num = img.page.number
        center = img.rectangle.center()
        content = img.image 

        output.setdefault(page_num, {"text": [], "images": []})
        output[page_num]["images"].append({"center": center, "content": content})

    return output



def parse(pdf_path, processing_dir=None, only_in_text=True):
    assert path.isfile(pdf_path)

    if not processing_dir:
        processing_dir = TemporaryDirectory(delete=False)
        
    output = []

    chunk_pdf(pdf_path, processing_dir if isinstance(processing_dir, str) else processing_dir.name)
    for x in sorted([ path.join(processing_dir if isinstance(processing_dir, str) else processing_dir.name, x) for x in listdir(processing_dir if isinstance(processing_dir, str) else processing_dir.name)], key= path.getmtime):

        if path.isfile(x) and path.basename(x).startswith(pdf_path.split(".")[0]):
            text_parser = ap.text.TextAbsorber()
            ap.Document(x).pages.accept(text_parser)
            parsed_text = text_parser.text
            parsed_content = parse_pagecontents(x)
            
            for page_nr, content in parsed_content.items():
                output.append([])
                aligned_content = align_intext_images(content["text"], content["images"], only_in_text=only_in_text)
                # print([ x.get("content") if not isinstance(x, str) else x for x in aligned_content ])

                for x in aligned_content:
                    if not isinstance(x["content"], str):
                        # output[-1].append(x)
                        output[-1].append(r"{Button}")

                    else:
                        try:
                            content_index = parsed_text.index(x["content"])
                        except Exception:
                            continue
                        output[-1].append(parsed_text[:content_index + len(x["content"])])
                        parsed_text = parsed_text[content_index + len(x["content"]):]

    return [ str.join("", x) for x in output ]


def serialize(dest, page_content):
    assert not path.isfile(dest)

    with open(dest, "w", newline="", encoding="utf-8") as f:
        csvwriter = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\n")
        csvwriter.writerow(["content"])

        for page in page_content:
            csvwriter.writerow([page.replace('\n', '\\n').replace('\r', '\\r')])





#### markdown generation ####

def convert_to_markdown(model, api_key, content: str, control_distance: float= None):
    prompt = prompt = """
Convert the following document completely into well-structured Markdown.

Focus on the following for your response:
- DO NOT EVER include remove or add text besides the original content provided
- The response should only enhance the provided text with Markdown formatting
- Do not include explainations or anything similar
- Preserve headings, lists, and tables
- Output valid Markdown only
- Respond ONLY with the contents of the Markdown

The document you should format into Markdown is the following:

{content}
"""
    content = content.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')
    generator = DeepInfraClient(model, api_key, timeout=300)
    markdown = generator.generate(prompt=prompt.format(content=content))

    if control_distance:
        __a = str.join("", (x for x in content if x.isalpha()))
        __b = str.join("", (x for x in markdown if x.isalpha()))
        dist = Levenshtein.distance(__a, __b)
        
        
        print(f"Generation had a text mismatch of: {dist / len(__a)}")
        if dist / len(__a) > control_distance:
            raise ValueError() #TODO: better err
    
    if markdown.startswith("```markdown") and markdown.endswith("```"):
        markdown = markdown[len("markdown'''"):-1 * len("'''")]

    return markdown



def parse_markdown(markdown):
    output = []

    splitter = MarkdownHeaderTextSplitter(
        [
            ("#", "main_topic"),
            ("##", "sub_topic"),
            ("###", "detailed_topic")
        ]
    )

    for x in splitter.split_text(markdown):
        output.append({key: value for key, value in x.metadata.items()} | {"data": x.page_content})
        
    return output



def process_pdf(input, output, api_key, markdown, split_markdown, control_distance):

    pdf_content = parse(input, None, True)

    if not markdown:
        serialize(output, pdf_content)

    else:
        markdown = convert_to_markdown(
            "mistralai/Mistral-Small-3.2-24B-Instruct-2506", 
            api_key, 
            str.join("", pdf_content),
            control_distance
        )
        if split_markdown:
            markdown = parse_markdown(markdown)
            markdown = pd.DataFrame(markdown).map(lambda x: str(x).replace("\n", "\\n").replace("\r", "\\r"))
            markdown = markdown[sorted(markdown.columns)]
            markdown = markdown.to_csv(None, index=False, lineterminator="\n")


        with open(output, "w", encoding="utf-8") as f:                
            f.write(markdown)











if __name__ == "__main__":
    from argparse import ArgumentParser

    argser = ArgumentParser("pdf-parser")
    argser.add_argument("input")
    argser.add_argument("output")
    argser.add_argument("--markdown", action="store_true", default=False)
    argser.add_argument("--split_markdown", action="store_true", default=False)
    argser.add_argument("--control_distance", type=float, default=None)
    argser.add_argument("--api_key", default=environ.get("DEEPINFRA_API_TOKEN", None))

    args = argser.parse_args()

    
    if not path.isfile(args.input):
        print(f"file: {"{args.input}"} doesn't exist")
        exit(1)

    if path.isfile(args.output):
        print(f"file: {"{args.output}"} already exists")
        exit(1)

    if args.markdown and not args.api_key:
        print(f"no key provided for generation")
        exit(1)

    try:
        process_pdf(
            args.input, 
            args.output, 
            args.api_key, 
            args.markdown, 
            args.split_markdown,
            args.control_distance
        )
    except Exception as e:
        print(f"failed: {e}")
        exit(1)