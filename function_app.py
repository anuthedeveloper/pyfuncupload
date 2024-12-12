import azure.functions as func
import logging
# from requests_toolbelt.multipart import decoder
# from azure.storage.blob import BlobServiceClient
import io
import os
import re
import cgi
import json

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "application/octet-stream",
    "multipart/form-data",
    "image/png"
}

# def get_pdf_text(pdf_stream: io.BytesIO) -> str:
#     """
#     Extract text from a PDF file in memory using PdfReader.
#     """
#     from pypdf import PdfReader
#     try:
#         reader = PdfReader(pdf_stream)
#         text = ""

#         # Loop through all pages to extract text
#         for page in reader.pages:
#             text += page.extract_text() or ""
#         return text
#     except Exception as e:
#         logging.error(f"Error extracting text from PDF: {str(e)}")
#         raise

# def upload_file_to_storage(file_data, file_name, content_type):
#     """
#     Uploads a file to Azure Blob Storage.
#     """
#     connection_string = "your_connection_string"
#     container_name = "your_container_name"
    
#     blob_service_client = BlobServiceClient.from_connection_string(connection_string)
#     container_client = blob_service_client.get_container_client(container_name)
    
#     blob_client = container_client.get_blob_client(blob=file_name)
#     blob_client.upload_blob(file_data, blob_type="BlockBlob", content_type=content_type)
#     logging.info(f"File {file_name} successfully uploaded to Blob Storage.")

def process_multipart_formdata(body, content_type):
    try:
        # Log the Content-Type for debugging
        logging.info(f"Content-Type received: {content_type}")
        # Fallback for unexpected content-types
        if 'multipart/form-data' not in content_type:
            return func.HttpResponse("Unsupported Content-Type.", status_code=400)

        # Parse multipart form-data
        multipart_data = decoder.MultipartDecoder(body, content_type)
        # Process each part
        for part in multipart_data.parts:
            content_disposition = part.headers.get(b'Content-Disposition', b'').decode()
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
                file_content = part.content
                logging.info(f"Received file: {filename}, Size: {len(file_content)} bytes")
                # You can process file_content as needed
                return func.HttpResponse(f"File {filename} uploaded successfully.", status_code=200)

        return func.HttpResponse("No file found in the requst", status_code=400)
        # # Wrap the file content in an in-memory file object
        # pdf_byte_stream = io.BytesIO(file_content)

        # # Process the PDF (Example: Extract text)
        # pdf_text = get_pdf_text(pdf_byte_stream)

        # # Log and return the extracted text
        # logging.info(f"Extracted text from {file_name}:\n{pdf_text}")
        # return func.HttpResponse(pdf_text, status_code=200, mimetype="text/plain")
    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        return func.HttpResponse(f"Error during file upload: {str(e)}", status_code=500)

def get_file_name_from_headers(req):
    content_disposition = req.headers.get("Content-Disposition", "")
    match = re.search(r'filename="(.+)"', content_disposition)
    if match:
        return match.group(1)  # Extracted file name from Content-Disposition
    return "uploaded_file"

def retrieve_filename(re1):
    # Retrieve the uploaded file's content and metadata
    file_stream = req.files.get("file")  # Access the file
    content_disposition = req.headers.get("Content-Disposition", "")
    
    # Extract the original file name from Content-Disposition header
    file_name = "uploaded_file"  # Default file name
    match = re.search(r'filename="(.+)"', content_disposition)
    if match:
        file_name = match.group(1)

    # If Content-Disposition isn't provided, fallback to file.stream.filename
    if not match and file_stream.filename:
        file_name = file_stream.filename

    return file_name


# Main entry
@app.route(route="http_trigger")
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    # name = req.params.get('file')
    # For debugging
    # logging.info(f"Headers: {req.headers}")
    # logging.info(f"Form: {req.form}")
    # logging.info(f"Raw Body: {req.get_body()}")
    try:
        # logging.info(f'Python HTTP trigger function request {req.get_body()}')
        # Extract the content type from headers
        content_type = req.headers.get('Content-Type', '')
        logging.info(f"Content Type: {content_type}")
        # Ensure the content type is multipart/form-data
        if 'multipart/form-data' not in content_type:
            return func.HttpResponse("Unsupported content type. Use multipart/form-data", status_code=400)

        # Parse the request body with werkzeug
        form = req.form  # Only works for simple form fields
        files = req.files  # Files need special handling

        # Check if a file was uploaded
        uploaded_file = None
        for key in files.keys():
            uploaded_file = files.get(key)
            break

        if uploaded_file is None:
            return func.HttpResponse("No file uploaded", status_code=400)
        
        file_name = uploaded_file.filename
        logging.info(f"File name {file_name}")
        # Read file content
        file_data = uploaded_file.read()
        # Determine file extension
        file_extension = file_name.split('.')[-1] if '.' in file_name else ''
        if not file_extension:
            return func.HttpResponse(
                "No file extension found in the uploaded file name.",
                status_code=400
            )

        # Validate file extension
        valid_extensions = ["png", "pdf", "doc"]
        if file_extension not in valid_extensions:
            return func.HttpResponse(
                f"Unsupported file extension: {file_extension}. "
                f"Supported extensions: {', '.join(valid_extensions)}",
                status_code=400
            )

        logging.info(f"File name: {file_name}, Extension: {file_extension}")
        # logging.info(f"Uploaded file: {file_name}, Extension: {file_extension}, Size: {len(file_data)} bytes")
        return func.HttpResponse(f"File {file_name} with extension {file_extension} and file date {file_data} uploaded successfully.", status_code=200)
    except Exception as e:
        logging.error(f"Error processing file: {e}")
        return func.HttpResponse(f"Error processing file: {str(e)}", status_code=500)




