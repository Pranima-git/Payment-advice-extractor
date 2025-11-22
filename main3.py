import os
import fitz
import json
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
#from pydantic import BaseModel
from openai import OpenAI

load_dotenv()


api_key = os.getenv("CEREBRAS_API_KEY")

# Cerebras client
client = OpenAI(
    api_key=api_key,
    base_url="https://api.cerebras.ai/v1"
)

# FastAPI app
app = FastAPI()

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    return full_text

# Endpoint to process PDF
@app.post("/extract_payment_advice")
async def extract_payment_advice(file: UploadFile = File(...)):
    # Save uploaded file temporarily
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    text_data = extract_text_from_pdf(file_path)

    # Prompt template

    prompt_template = """
{
"status": "success",
"message": "Payment Advice processed successfully",
"data": {
"doc_number": null,
"payment_date": null,
"total_amount": null,
"account_number": null,
"company_name": null,
"issuer_company": "Reliance Retail Limited",
"payment_details": [
{
"doc_no": null,
"invoice_ref": null,
"document_amount": null,
"payment_amount": null,
"doc_date": null,
"invoice_date": null,
"is_deduction": false
}
],
"document_type": "payment_advice",
"extraction_timestamp": null,
"source_file": null,
"success": true
}
}
You are a precise document processing assistant specialized in extracting structured data from payment advice documents issued by Reliance Retail Limited. Your task is to analyze the provided payment advice document text and extract ALL payment entries, including regular payments, TDS deductions, and GST TAX HOLD/PAID entries from ALL pages. Return the result in the JSON format specified above and NOTHING ELSE.

The document has a table structure with the following columns:
Doc. No. | Inv./Ref. Doc.No. | Inv./Ref Doc. Amt. | Payment Amount
Doc. Date | Inv./Ref. Doc.Date | |
Narration | | |

CRITICAL FIELD MAPPING:
"doc_no": Extract from "Doc. No." (e.g., "12398531", "4370446419")
"invoice_ref": Extract from "Inv./Ref. Doc.No." (e.g., "CK3052-FY26")
"document_amount": Extract from "Inv./Ref Doc. Amt." (e.g., "9,487.00"). Set to null if blank or not present.
"payment_amount": Extract from "Payment Amount" (e.g., "9,478.96", "-2,797.12"). Set to null if blank or not present.
"doc_date": Extract from "Doc. Date" in exact format (e.g., "07.07.2025")
"invoice_date": Extract from "Inv./Ref. Doc.Date" in exact format (e.g., "03.07.2025")
"tds_amount": Extract from "Narration" if explicitly mentioned as "(TDS Amount X.XX-)" (e.g., "4.00-"). Do not include the field if not present or for GST entries.
"is_deduction":
- Include this field for GST TAX HOLD entries (true) and GST TAX PAID entries (false).
- Include this field for regular payments only if there is NO tds_amount.
- Omit this field entirely if tds_amount is present.

NARRATION HANDLING:
Only include the "narration" field in "payment_details" for entries with "GST TAX HOLD" or "GST TAX PAID" in the Narration column.
For TDS entries (e.g., containing "(TDS Amount 4.00-)") and regular payments, DO NOT include the "narration" field in the JSON output, even as null.
For GST entries, set "narration" to the exact value (e.g., "GST TAX HOLD", "GST TAX PAID").

SPECIAL HANDLING FOR ENTRIES:
Regular Payment Entries:
Include: doc_no, invoice_ref, doc_date, invoice_date, document_amount, payment_amount, tds_amount (if present), and is_deduction (false) *only if no tds_amount is present*.
Example: "12398531 CK3052-FY26 9487.00 9,478.96" with "(TDS Amount 8.04-)" → "document_amount": "9,487.00", "payment_amount": "9,478.96", "tds_amount": "8.04-" (no is_deduction field in this case).

GST TAX HOLD Entries:
Identified by "Narration" containing "GST TAX HOLD" and negative payment amount (e.g., "-2,797.12").
Include: doc_no, invoice_ref, doc_date, invoice_date, document_amount (null), payment_amount (e.g., "-2,797.12"), narration ("GST TAX HOLD"), is_deduction (true). Do not include "tds_amount".

GST TAX PAID Entries:
Identified by "Narration" containing "GST TAX PAID" and positive payment amount.
Include: doc_no, invoice_ref, doc_date, invoice_date, document_amount (if present, else null), payment_amount, narration ("GST TAX PAID"), is_deduction (false). Do not include "tds_amount".

STRICT INSTRUCTIONS:
DO NOT guess or infer missing data. If a value cannot be located with certainty, return null.
Preserve numbers exactly as in the document, including commas, decimal points, minus signs, and trailing hyphens for negative amounts (e.g., "9,487.00", "2,797.12-").
Never copy a value into both "document_amount" and "payment_amount" for the same entry.
Dates: Copy exactly as shown (e.g., "07.07.2025"). If only one date is found, fill that and leave the other null.
TDS: Only extract "tds_amount" from "Narration" if explicitly stated as "(TDS Amount X.XX-)". Preserve exact format (e.g., "4.00-"). Include the "tds_amount" field only if a value is extracted; otherwise, exclude it entirely.
Payment Details:
Extract each table row as a separate object in the "payment_details" array.
Maintain the order as they appear in the document.
Do not merge entries.

Header Fields:
"doc_number": Extract the settlement document number (e.g., "4200112633/2025").
"payment_date": Extract from "Date" (e.g., "11.07.2025").
"total_amount": Extract from "Total INR" (e.g., "99,951.76"), without currency symbol.
"account_number": Extract from "Your A/c with us" (e.g., "20001756").
"company_name": Extract the vendor name with full suffix (e.g., "COMBINED FOODS (P) LIMITED").
"extraction_timestamp": Set to current timestamp in ISO format (e.g., "2025-08-12T12:18:00+05:30").
"source_file": Use the provided source file name (e.g., "{source_file}").

Output:
Return ONLY the JSON structure specified above, with no additional text, commentary, or markdown.
For TDS and regular payment entries, exclude the "narration" field entirely from the JSON object.
For all entries, exclude the "tds_amount" field if no TDS amount is extracted.
Omit the "is_deduction" field entirely if tds_amount is present.
If multiple pages exist, combine all entries in the "payment_details" array in document order.

PDF TEXT FROM ALL PAGES:
{pdf_text}
"""

    # Combine prompt with extracted text
    final_prompt = f"{prompt_template}\n\n{text_data}"

    # Call GPT-OSS-120B from Cerebras
    response = client.chat.completions.create(
        model="gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You are a data extraction assistant."},
            {"role": "user", "content": final_prompt}
        ],
        temperature=0.2,
        max_tokens=11192,
        stop=None,
    )

    # Delete temp file
    os.remove(file_path)

    raw_output = response.choices[0].message.content

    # Parse to JSON so Postman gets proper object, not escaped string
    try:
        parsed_output = json.loads(raw_output)
    except json.JSONDecodeError:
        parsed_output = {"raw_text": raw_output}

    return parsed_output