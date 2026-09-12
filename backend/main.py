import os
import shutil
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
from docx import Document
from openai import OpenAI


# ============================================================
# CONFIGURATION
# ============================================================

APP_NAME = "TransformAI API"

# Ollama local API
OLLAMA_BASE_URL = "http://localhost:11434/v1"

# Fast/small local model
MODEL_NAME = "qwen3:1.7b"

# Ollama uses an API key value internally,
# but this is NOT an OpenAI API key.
client = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="ollama"
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=APP_NAME,
    description="TransformAI backend using Ollama",
    version="2.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# UPLOAD DIRECTORY
# ============================================================

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# ============================================================
# BASIC ROUTES
# ============================================================

@app.get("/")
def root():

    return {
        "message": "TransformAI backend is running",
        "status": "success",
        "provider": "Ollama",
        "model": MODEL_NAME
    }


@app.get("/health")
def health():

    return {
        "status": "healthy",
        "provider": "Ollama",
        "model": MODEL_NAME,
        "ollama_url": OLLAMA_BASE_URL
    }


# ============================================================
# FILE TEXT EXTRACTION
# ============================================================

def extract_text_from_file(file_path: str) -> str:

    path = Path(file_path)

    extension = path.suffix.lower()

    try:

        # ----------------------------------------------------
        # PDF
        # ----------------------------------------------------

        if extension == ".pdf":

            reader = PdfReader(file_path)

            pages = []

            for page in reader.pages:

                page_text = page.extract_text()

                if page_text:
                    pages.append(page_text)

            return "\n".join(pages)


        # ----------------------------------------------------
        # DOCX
        # ----------------------------------------------------

        elif extension == ".docx":

            document = Document(file_path)

            paragraphs = []

            for paragraph in document.paragraphs:

                text = paragraph.text.strip()

                if text:
                    paragraphs.append(text)

            return "\n".join(paragraphs)


        # ----------------------------------------------------
        # TXT
        # ----------------------------------------------------

        elif extension == ".txt":

            return path.read_text(
                encoding="utf-8",
                errors="ignore"
            )


        # ----------------------------------------------------
        # Unsupported
        # ----------------------------------------------------

        return ""

    except Exception as e:

        print("File extraction error:", e)

        return ""


# ============================================================
# SAVE UPLOADED FILE
# ============================================================

async def save_uploaded_file(
    file: UploadFile | None
) -> str:

    if file is None:
        return ""

    if not file.filename:
        return ""

    allowed_extensions = {
        ".pdf",
        ".docx",
        ".txt"
    }

    extension = Path(file.filename).suffix.lower()

    if extension not in allowed_extensions:

        raise ValueError(
            "Only PDF, DOCX and TXT files are supported."
        )

    filename = Path(file.filename).name

    file_path = UPLOAD_DIR / filename

    with open(file_path, "wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    return str(file_path)


# ============================================================
# BUILD SOURCE CONTEXT
# ============================================================

def build_context(
    source_text: str,
    uploaded_file_text: str
) -> str:

    parts = []

    if source_text and source_text.strip():

        parts.append(
            "USER PROVIDED SOURCE:\n"
            + source_text.strip()
        )

    if uploaded_file_text and uploaded_file_text.strip():

        parts.append(
            "UPLOADED FILE CONTENT:\n"
            + uploaded_file_text.strip()
        )

    if not parts:

        return "No source material was provided."

    return "\n\n".join(parts)


# ============================================================
# OLLAMA GENERATION
# ============================================================

def generate_with_ollama(
    prompt: str,
    max_tokens: int = 1800
) -> str:

    try:

        print("\n========================================")
        print("OLLAMA REQUEST")
        print("Model:", MODEL_NAME)
        print("========================================")

        response = client.chat.completions.create(

            model=MODEL_NAME,

            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are TransformAI. "
                        "You are a fast, accurate and professional "
                        "content transformation assistant. "
                        "Follow the user's instructions exactly."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.4,

            max_tokens=max_tokens
        )

        answer = response.choices[0].message.content

        if not answer:

            raise Exception(
                "Ollama returned an empty response."
            )

        return answer.strip()

    except Exception as e:

        print("\n========================================")
        print("OLLAMA ERROR")
        print("========================================")
        print(str(e))
        print("========================================\n")

        raise Exception(
            "Could not generate content using Ollama. "
            "Make sure Ollama is running and qwen3:1.7b "
            "is installed."
        )


# ============================================================
# REFINE PROMPT
# ============================================================

@app.post("/api/refine-prompt")
async def refine_prompt(

    raw_prompt: str = Form(""),

    source_text: str = Form(""),

    audience: str = Form("General Audience"),

    tone: str = Form("Professional"),

    language: str = Form("English"),

    objective: str = Form("Inform"),

    detail: str = Form("3"),

    file: UploadFile | None = File(None)

):

    try:

        # ----------------------------------------------------
        # Extract uploaded file
        # ----------------------------------------------------

        uploaded_file_text = ""

        if file is not None:

            file_path = await save_uploaded_file(file)

            if file_path:

                uploaded_file_text = (
                    extract_text_from_file(file_path)
                )


        # ----------------------------------------------------
        # Build context
        # ----------------------------------------------------

        context = build_context(
            source_text,
            uploaded_file_text
        )


        # ----------------------------------------------------
        # Check raw prompt
        # ----------------------------------------------------

        if not raw_prompt.strip():

            return {
                "success": False,
                "error": "Please enter a prompt."
            }


        # ----------------------------------------------------
        # Prompt for Qwen
        # ----------------------------------------------------

        prompt = f"""
You are an expert prompt engineer.

Transform the user's broken or incomplete prompt into a
clear, high-quality, professional AI prompt.

ORIGINAL PROMPT:
{raw_prompt}

TARGET AUDIENCE:
{audience}

TONE:
{tone}

LANGUAGE:
{language}

OBJECTIVE:
{objective}

DETAIL LEVEL:
{detail}

SOURCE MATERIAL:
{context}

REQUIREMENTS:

- Understand the original intention.
- Preserve the user's meaning.
- Fix ambiguity.
- Add useful missing instructions.
- Clearly describe the expected output.
- Include the target audience.
- Include the requested tone.
- Include the requested language.
- Include the objective.
- Use the source material when available.
- Make the prompt actionable.
- Do not generate the final answer.
- Do not explain your changes.
- Return ONLY the refined prompt.

REFINED PROMPT:
"""

        # ----------------------------------------------------
        # Generate
        # ----------------------------------------------------

        refined = generate_with_ollama(
            prompt,
            max_tokens=1000
        )


        return {
            "success": True,
            "refined_prompt": refined
        }


    except Exception as e:

        print(
            "Refine prompt error:",
            str(e)
        )

        return {
            "success": False,
            "error": str(e)
        }


# ============================================================
# OUTPUT INSTRUCTIONS
# ============================================================

def get_output_instruction(
    output_type: str
) -> str:

    instructions = {

        "Executive Summary":
        """
Create a concise executive summary.
Include:
- Key message
- Important findings
- Main insights
- Recommendations
- Conclusion
""",

        "Advisory":
        """
Create a professional advisory.
Include:
- Situation
- Key issues
- Analysis
- Risks
- Recommended actions
- Conclusion
""",

        "LinkedIn Post":
        """
Create an engaging professional LinkedIn post.
Include:
- Strong hook
- Main message
- Useful insights
- Conclusion
- A few relevant hashtags
""",

        "X Thread":
        """
Create a concise X/Twitter thread.
Include:
- Strong opening
- Numbered posts
- Logical flow
- Key insights
- Strong conclusion
""",

        "Presentation":
        """
Create presentation content.

For each slide provide:
- Slide title
- Main bullet points

Suggested structure:
1. Title
2. Introduction
3. Background
4. Key information
5. Analysis
6. Insights
7. Recommendations
8. Conclusion
""",

        "Infographic":
        """
Create concise infographic content.
Include:
- Main title
- Important facts
- Key points
- Short explanations
- Final takeaway
""",

        "Video Package":
        """
Create a video content package.
Include:
- Video title
- Hook
- Introduction
- Scene structure
- Narration
- On-screen text
- Visual suggestions
- Closing
""",

        "Report":
        """
Create a professional report.
Include:
- Title
- Executive Summary
- Introduction
- Background
- Key Findings
- Analysis
- Recommendations
- Conclusion
"""
    }

    return instructions.get(
        output_type,
        "Create a professional output based on the refined prompt."
    )


# ============================================================
# PARSE GENERATED OUTPUTS
# ============================================================

def parse_outputs(
    result: str,
    output_list: list[str]
) -> dict:

    generated_outputs = {}

    current_output = None

    current_content = []

    # --------------------------------------------------------
    # Possible heading formats
    # --------------------------------------------------------

    for line in result.splitlines():

        clean = line.strip()

        if not clean:

            if current_output is not None:
                current_content.append("")

            continue


        found_output = None


        for output_name in output_list:

            variations = [

                output_name.lower(),

                f"[{output_name.lower()}]",

                f"## {output_name.lower()}",

                f"### {output_name.lower()}",

                f"**{output_name.lower()}**"

            ]

            if clean.lower() in variations:

                found_output = output_name

                break


        # ----------------------------------------------------
        # New section found
        # ----------------------------------------------------

        if found_output:

            if current_output is not None:

                generated_outputs[
                    current_output
                ] = "\n".join(
                    current_content
                ).strip()


            current_output = found_output

            current_content = []

        else:

            if current_output is not None:

                current_content.append(line)


    # --------------------------------------------------------
    # Save last output
    # --------------------------------------------------------

    if current_output is not None:

        generated_outputs[
            current_output
        ] = "\n".join(
            current_content
        ).strip()


    # --------------------------------------------------------
    # If parsing failed
    # --------------------------------------------------------

    if not generated_outputs:

        if len(output_list) == 1:

            generated_outputs[
                output_list[0]
            ] = result.strip()

        else:

            # Put the complete response into first output
            generated_outputs[
                output_list[0]
            ] = result.strip()


    return generated_outputs


# ============================================================
# TRANSFORM CONTENT
# ============================================================

@app.post("/api/transform")
async def transform_content(

    refined_prompt: str = Form(""),

    source_text: str = Form(""),

    audience: str = Form("General Audience"),

    tone: str = Form("Professional"),

    language: str = Form("English"),

    objective: str = Form("Inform"),

    detail: str = Form("3"),

    outputs: str = Form(""),

    file: UploadFile | None = File(None)

):

    try:

        # ----------------------------------------------------
        # Extract uploaded file
        # ----------------------------------------------------

        uploaded_file_text = ""

        if file is not None:

            file_path = await save_uploaded_file(file)

            if file_path:

                uploaded_file_text = (
                    extract_text_from_file(file_path)
                )


        # ----------------------------------------------------
        # Build context
        # ----------------------------------------------------

        context = build_context(
            source_text,
            uploaded_file_text
        )


        # ----------------------------------------------------
        # Validate refined prompt
        # ----------------------------------------------------

        if not refined_prompt.strip():

            return {
                "success": False,
                "error": "Refined prompt is required."
            }


        # ----------------------------------------------------
        # Get selected outputs
        # ----------------------------------------------------

        output_list = [

            item.strip()

            for item in outputs.split(",")

            if item.strip()

        ]


        if not output_list:

            output_list = [
                "Executive Summary"
            ]


        # ----------------------------------------------------
        # Create instructions
        # ----------------------------------------------------

        output_sections = []

        for output_name in output_list:

            instruction = get_output_instruction(
                output_name
            )

            output_sections.append(
                f"""
OUTPUT TYPE:
{output_name}

INSTRUCTIONS:
{instruction}
"""
            )


        all_output_instructions = "\n".join(
            output_sections
        )


        # ----------------------------------------------------
        # ONE REQUEST FOR ALL OUTPUTS
        # ----------------------------------------------------

        prompt = f"""
You are TransformAI.

Generate ALL requested outputs in ONE response.

REFINED PROMPT:
{refined_prompt}

TARGET AUDIENCE:
{audience}

TONE:
{tone}

LANGUAGE:
{language}

OBJECTIVE:
{objective}

DETAIL LEVEL:
{detail}

SOURCE MATERIAL:
{context}

REQUESTED OUTPUTS:
{all_output_instructions}

IMPORTANT RULES:

1. Generate every requested output.
2. Keep outputs clearly separated.
3. Use the exact output type as a heading.
4. Follow the refined prompt.
5. Use the source material where appropriate.
6. Do not invent important facts.
7. Use the requested language.
8. Use the requested tone.
9. Keep content useful and reasonably concise.
10. Do not explain your process.
11. Return ONLY the generated content.

MANDATORY FORMAT:

[Executive Summary]
content

[Advisory]
content

[LinkedIn Post]
content

[...other requested outputs...]

Only include sections that were requested.
"""


        print("\n========================================")
        print("GENERATING ALL OUTPUTS")
        print("========================================")

        print(
            "Selected outputs:",
            output_list
        )

        print(
            "Using model:",
            MODEL_NAME
        )


        # ----------------------------------------------------
        # SINGLE AI CALL
        # ----------------------------------------------------

        result = generate_with_ollama(
            prompt,
            max_tokens=2500
        )


        # ----------------------------------------------------
        # Parse outputs
        # ----------------------------------------------------

        generated_outputs = parse_outputs(
            result,
            output_list
        )


        # ----------------------------------------------------
        # Make sure requested outputs exist
        # ----------------------------------------------------

        for output_name in output_list:

            if output_name not in generated_outputs:

                generated_outputs[
                    output_name
                ] = (
                    "This output could not be separated "
                    "from the generated response."
                )


        print("\nGeneration completed successfully.\n")


        # ----------------------------------------------------
        # Send response to frontend
        # ----------------------------------------------------

        return {

            "success": True,

            "outputs": generated_outputs

        }


    except Exception as e:

        print("\n========================================")
        print("TRANSFORM ERROR")
        print("========================================")

        print(str(e))

        print("========================================\n")


        return {

            "success": False,

            "error": str(e)

        }


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )