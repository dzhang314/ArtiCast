#!/usr/bin/env python3
# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false

import os
import sys
from google.genai import Client as GeminiClient
from google.genai.types import GenerateContentConfig, GenerateContentResponse
from grobid_client.grobid_client import GrobidClient
from xml.etree.ElementTree import Element, fromstring


GEMINI_CLIENT: GeminiClient = GeminiClient(api_key=os.getenv("GEMINI_API_KEY"))
GROBID_CLIENT: GrobidClient = GrobidClient(grobid_server="http://localhost:8070")


SYSTEM_PROMPT = """\
You are an academic audiobook editor. Your task is to transform rough text \
mechanically extracted from PDF files of academic papers into clean, \
well-formatted scripts suitable for audiobook narration.

You will be provided with rough text that may contain OCR errors, formatting \
artifacts, and the following special placeholders:
 - [[HEADING: <title>]] represents a section or subsection heading.
 - [[FORMULA: <content>]] represents a mathematical formula.

You must process the rough text into a clean, well-formatted script that is \
natural and smooth to read aloud. This includes, and is not limited to, the \
following modifications:

1. Correct spelling and grammar errors.
2. Remove text that is not part of the main body of the paper, \
such as page numbers, running headers, and bibliographic information.
3. Rephrase parenthetical statements to be spoken aloud.
4. Announce headings clearly. For example, "[[HEADING: IV. Data Analysis]]" \
should be verbalized as "Section Four: Data Analysis."
5. Remove references to figures, tables, citations, and other non-textual \
features whenever the omission does not impact the flow of the text.
6. When possible, replace phrases and abbreviations used in writing with more \
idiomatic phrases used in speech. For example, replace "i.e." with "that is" \
and "e.g." with "for example".
7. Spell out abbreviations in full (e.g., replace "eV" with "electron volt") \
unless the concept is better known by its initialism than its full name, \
such as "DNA" or "TCP".
8. Translate formulas from "[[FORMULA: <content>]]" into clear spoken English. \
For example, replace "[[FORMULA: E = m c 2]]" with "energy equals mass times \
the speed of light squared". If a formula is too complicated to be read aloud \
succinctly, state that a long formula has been omitted and provide a brief, \
high-level summary of its purpose.

Your goal is to translate the rough text into a polished script for audio \
narration. You MUST NOT add any new substantive content or interpretation. \
Adhere as closely as possible to the original text you are given, and make \
only the minimal edits necessary to satisfy these requirements.
"""


def is_heading(element: Element) -> bool:
    return element.tag == "{http://www.tei-c.org/ns/1.0}head"


def is_paragraph(element: Element) -> bool:
    return element.tag == "{http://www.tei-c.org/ns/1.0}p"


def is_formula(element: Element) -> bool:
    return element.tag == "{http://www.tei-c.org/ns/1.0}formula"


def is_bib_reference(element: Element) -> bool:
    return (
        element.tag == "{http://www.tei-c.org/ns/1.0}ref"
        and element.get("type") == "bibr"
    )


def process_paper_section(section: Element) -> list[str]:
    if section.tag == "{http://www.tei-c.org/ns/1.0}note":
        # Notes are skipped. These usually contain copyright or
        # bibliographic information that should not be narrated.
        return []
    elif section.tag == "{http://www.tei-c.org/ns/1.0}figure":
        # For now, figures and captions are ignored.
        # In the future, figures and captions should be provided
        # to the LLM as additional context outside the main text,
        # but we do not yet have a system for separating main text
        # from supplementary text used only to edit the main text.
        return []
    elif section.tag == "{http://www.tei-c.org/ns/1.0}div":
        result: list[str] = []
        for element in section.iter():
            if is_heading(element):
                assert element.text is not None
                result.append("[[HEADING: " + element.text.strip() + "]]")
            elif is_paragraph(element):
                assert element.text is None
                assert element.tail is None
                result.append("")
            elif is_formula(element):
                assert element.text is not None
                result.append("[[FORMULA: " + element.text.strip() + "]]")
            elif is_bib_reference(element):
                # For now, bibliographic references like [4] are skipped,
                # since they tend not to be useful for narration without
                # explicitly referencing the bibliography. In the future,
                # it would be preferable to manually dereference them and
                # provide the cited authors and title to the LLM.
                pass
            else:
                text: str | None = element.text
                if text is not None:
                    text = text.strip()
                if text:
                    result.append(text)
            tail: str | None = element.tail
            if tail is not None:
                tail = tail.strip()
            if tail:
                result.append(tail)
        return result
    else:
        raise ValueError(f"Unexpected section tag: {section.tag}")


def main(input_pdf_path: str) -> None:

    assert os.path.isfile(input_pdf_path)
    if not input_pdf_path.lower().endswith(".pdf"):
        print("WARNING: Input file should be a PDF.", file=sys.stderr)

    print(f"Preprocessing {input_pdf_path} with GROBID...")
    status: int
    grobid_result: str
    _, status, grobid_result = GROBID_CLIENT.process_pdf(  # pyright: ignore
        service="processFulltextDocument",
        pdf_file=input_pdf_path,
        generateIDs=False,
        consolidate_header=False,
        consolidate_citations=False,
        include_raw_citations=False,
        include_raw_affiliations=False,
        tei_coordinates=False,
        segment_sentences=True,
    )
    assert status == 200
    print("GROBID preprocessing completed.")

    print("Extracting rough text...")
    tree: Element = fromstring(grobid_result)
    (text_element,) = tree.findall("{http://www.tei-c.org/ns/1.0}text")
    (body_element,) = text_element.findall("{http://www.tei-c.org/ns/1.0}body")

    rough_sections: list[list[str]] = []
    for section in body_element:
        rough_sections.append(process_paper_section(section))
    rough_text: list[str] = []
    for section in rough_sections:
        if rough_text:
            rough_text.append("")
        rough_text.extend(section)
    print("Rough text extraction completed.")

    print("Revising rough text with Gemini...")
    response: GenerateContentResponse = GEMINI_CLIENT.models.generate_content(
        model="gemini-2.5-pro",
        config=GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
        contents="\n".join(rough_text),
    )
    print("Gemini response received.")
    print(response.usage_metadata)

    assert response.candidates is not None
    (candidate,) = response.candidates
    assert candidate.content is not None
    assert candidate.content.parts is not None
    (part,) = candidate.content.parts
    assert part.text is not None
    revised_text: str = part.text.strip()

    print("Saving revised text...")
    output_path: str = os.path.splitext(input_pdf_path)[0] + ".txt"
    with open(output_path, "w") as f:
        _ = f.write(revised_text)
    print(f"Revised text saved to {output_path}.")

    print()
    print(revised_text)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: ArtiCast.py <input_pdf_path>")
        sys.exit(1)
    main(sys.argv[1])
