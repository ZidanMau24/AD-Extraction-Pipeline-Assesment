# Gradio Web Interface for AD Extraction

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the App
```bash
python app.py
```

The app will launch at: **http://localhost:7860**

## 📋 How to Use

### Interface Components

1. **📄 Upload Document**
   - Click the upload area or drag-and-drop your AD PDF file
   - Supported format: `.pdf`

2. **🏢 Issuing Authority**
   - Select either "FAA" or "EASA" from the dropdown
   - This determines which extraction logic to use

3. **🔍 Extract Document Button**
   - Click to process the uploaded PDF
   - Extraction takes 5-10 seconds

4. **📊 Extraction Output**
   - View the structured JSON output
   - Includes:
     - AD metadata (ID, authority, effective date, manufacturer)
     - Applicability rules (aircraft models, MSN constraints)
     - Modification exclusions
     - Raw applicability text

### Example Workflow

1. Click "Load FAA AD 2025-23-53" or "Load EASA AD 2025-0254" button
2. The PDF and authority will be auto-selected
3. Click "🔍 Extract Document"
4. View the extracted rules in JSON format

## 📊 Example Output

```json
{
  "ad_id": "FAA-2025-23-53",
  "issuing_authority": "FAA",
  "effective_date": "December 18, 2024",
  "manufacturer": "Boeing",
  "applicability_rules": [
    {
      "aircraft_models": ["MD-11", "MD-11F"],
      "msn_constraint": {
        "type": "all",
        "min_msn": null,
        "max_msn": null,
        "specific_msns": null
      },
      "excluded_if_modifications": [],
      "required_modifications": []
    }
  ],
  "raw_applicability_text": "..."
}
```

## 🎯 Features

✅ **Drag-and-drop upload** - Easy file selection  
✅ **Authority selection** - FAA or EASA  
✅ **Real-time extraction** - Process PDFs on-the-fly  
✅ **Structured JSON output** - Clean, validated data  
✅ **Example buttons** - Quick testing with provided ADs  
✅ **Error handling** - Clear error messages  

## 🔧 Technical Details

- **Framework**: Gradio 4.0+
- **PDF Processing**: Docling
- **Data Validation**: Pydantic
- **Extraction**: Regex-based parsing with FAA/EASA extractors

## 📝 Notes

- The app runs locally and does not send data to external servers
- Processing time depends on PDF size (typically 5-10 seconds)
- Large PDFs (>10MB) may take longer to process

## 🐛 Troubleshooting

**Issue**: App won't start
- **Solution**: Make sure all dependencies are installed: `pip install -r requirements.txt`

**Issue**: Extraction fails
- **Solution**: Verify the PDF is a valid AD document and the correct authority is selected

**Issue**: Port 7860 already in use
- **Solution**: Edit `app.py` and change `server_port=7860` to another port
