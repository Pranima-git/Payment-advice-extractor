# Payment Advice Extractor (FastAPI + Python + Cerebras)

This project extracts **structured payment advice data** from PDFs.  
It reads the PDF, extracts text, and uses the **Cerebras GPT-OSS-120B** model to convert the unstructured table into a clean JSON format.

---

## Features

✔ Extracts text from multi-page PDFs using **PyMuPDF (fitz)**  
✔ Sends extracted text to **Cerebras LLM API**  
✔ Returns **accurate structured JSON** containing:
- Header details (doc number, payment date, account number, vendor)
- Regular payment entries  
- GST TAX HOLD / GST TAX PAID entries  
- TDS deduction entries  
✔ Strict formatting with:
- Exact numbers  
- Exact dates  
- No guessing/missing values=returned as null  
✔ FastAPI API endpoint for easy integration  
✔ Works with Postman, Streamlit, or any frontend

---

##  Technology Stack

- **Python 3.10+**
- **FastAPI**
- **PyMuPDF (`fitz`)** for PDF parsing
- **Cerebras OpenAI-Compatible API**
- **Uvicorn** server
- **dotenv**
- **JSON**

---

## Sample Output(Json)
```json
{
"status": "success",
"data": {
"doc_number": "4200407781/2025",
"payment_date": "11.07.2025",
"total_amount": "53,335.13",
"account_number": "20001756",
"company_name": "COMBINED FOODS (P) LIMITED",
"document_type": "payment_advice",
"payment_details": [
{
"doc_no": "11172260",
"invoice_ref": "CK2236-FY26",
"document_amount": "11,723.00",
"payment_amount": "11,713.05",
"doc_date": "07.07.2025",
"invoice_date": "03.06.2025",
"tds_amount": "9.95-"
},
{
"doc_no": "4370446419",
"invoice_ref": "CK3076-FY26",
"payment_amount": "-2,797.12",
"doc_date": "07.07.2025",
"invoice_date": "04.07.2025",
"narration": "GST TAX HOLD",
"is_deduction": true
}
]
}
}
```
