# Local OCR setup

Tarjan-RAG uses the free, locally run Tesseract OCR engine for image uploads and scanned PDF pages. No OCR service is called and no OCR usage fee is incurred. Scanned PDF pages are rendered by the existing PDF parser and passed to Tesseract; text PDFs stay on the normal extraction path.

## Windows

Install Tesseract with winget:

```powershell
winget install -e --id tesseract-ocr.tesseract
```

Open a new PowerShell window and verify the executable and English language data:

```powershell
tesseract --version
tesseract --list-langs
```

Restart the Tarjan-RAG backend after installation. If `tesseract.exe` is not on `PATH`, set `TESSERACT_CMD` to its full path (commonly `C:\Program Files\Tesseract-OCR\tesseract.exe`).

## macOS and Linux

Install Tesseract with the platform package manager (`brew install tesseract` on macOS, `sudo apt install tesseract-ocr` on Debian/Ubuntu), verify `tesseract --version`, then restart the backend.

## OCR language

English is the default (`TESSERACT_LANG=eng`). Set `TESSERACT_LANG` to one or more installed language codes joined with `+`, for example `eng+hin`.

Supported direct image inputs: PNG, JPG/JPEG, TIFF, and BMP. For PDFs, pages with little or no extractable text are OCRed; existing text pages are retained. OCR output is marked with its PDF page number in the extracted source text.

If Tesseract is unavailable, scanned-only PDFs and image uploads return an actionable setup error. Ordinary text PDFs and documents continue to ingest without OCR.

References: [Tesseract installation](https://tesseract-ocr.github.io/tessdoc/Installation.html), [Tesseract input formats](https://tesseract-ocr.github.io/tessdoc/InputFormats.html).
