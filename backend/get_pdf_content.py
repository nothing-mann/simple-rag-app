"""
PDF Content Extractor for Heritage Learning Assistant

This module extracts text content from PDF documents and saves it as text files
in the transcripts directory, following the same pattern as the YouTube transcripts.
"""

import os
import sys
import argparse
from PyPDF2 import PdfReader
import re
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can import from backend
from backend.config import TRANSCRIPTS_DIR

class PDFContentExtractor:
    def __init__(self, output_dir: str = TRANSCRIPTS_DIR):
        """Initialize the PDF Content Extractor
        
        Args:
            output_dir: Directory to save extracted text (defaults to TRANSCRIPTS_DIR)
        """
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from a PDF file
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            reader = PdfReader(pdf_path)
            text_content = []
            
            # Extract text from each page
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:  # Only add non-empty pages
                    text_content.append(f"--- Page {page_num + 1} ---\n{text}")
            
            return "\n\n".join(text_content)
            
        except Exception as e:
            print(f"Error extracting text from PDF {pdf_path}: {str(e)}")
            return ""
    
    def save_text_to_file(self, text_content: str, output_filename: str = None, pdf_path: str = None) -> str:
        """Save extracted text to a file
        
        Args:
            text_content: The extracted text to save
            output_filename: Optional filename override
            pdf_path: Original PDF path for deriving filename
            
        Returns:
            Path to the saved file
        """
        if not text_content:
            print("No content to save")
            return None
            
        # Generate filename based on PDF filename if not provided
        if not output_filename and pdf_path:
            # Get the filename without extension
            base_name = Path(pdf_path).stem
            # Clean the filename (remove spaces, special chars)
            clean_name = re.sub(r'[^\w\-]', '_', base_name.lower())
            # Add .txt extension
            output_filename = f"{clean_name}.txt"
        
        # If still no filename, use timestamp
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"pdf_extract_{timestamp}.txt"
        
        # Ensure the filename has a .txt extension
        if not output_filename.endswith('.txt'):
            output_filename += '.txt'
            
        # Create the full output path
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Write content to file
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(text_content)
            print(f"Content saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"Error saving content to file: {str(e)}")
            return None
    
    def process_pdf(self, pdf_path: str, output_filename: str = None) -> str:
        """Process a PDF file - extract text and save to a file
        
        Args:
            pdf_path: Path to the PDF file
            output_filename: Optional custom filename for the output text file
            
        Returns:
            Path to the saved text file, or None if processing failed
        """
        print(f"Processing PDF: {pdf_path}")
        
        # Check if file exists
        if not os.path.isfile(pdf_path):
            print(f"Error: PDF file not found at {pdf_path}")
            return None
        
        # Extract text
        text_content = self.extract_text_from_pdf(pdf_path)
        
        if not text_content:
            print("Error: Failed to extract text or PDF had no text content")
            return None
            
        # Save to file
        return self.save_text_to_file(text_content, output_filename, pdf_path)
    
    def process_directory(self, pdf_dir: str) -> list:
        """Process all PDF files in a directory
        
        Args:
            pdf_dir: Directory containing PDF files
            
        Returns:
            List of paths to saved text files
        """
        if not os.path.isdir(pdf_dir):
            print(f"Error: Directory not found: {pdf_dir}")
            return []
            
        pdf_files = [os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) 
                    if f.lower().endswith('.pdf') and os.path.isfile(os.path.join(pdf_dir, f))]
        
        if not pdf_files:
            print(f"No PDF files found in {pdf_dir}")
            return []
            
        saved_files = []
        for pdf_file in pdf_files:
            output_path = self.process_pdf(pdf_file)
            if output_path:
                saved_files.append(output_path)
                
        return saved_files

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description='Extract text from PDF documents')
    parser.add_argument('--pdf', type=str, help='Path to a single PDF file to process')
    parser.add_argument('--dir', type=str, help='Directory containing PDF files to process')
    parser.add_argument('--output', type=str, help='Custom filename for the output text file')
    
    args = parser.parse_args()
    
    extractor = PDFContentExtractor()
    
    if args.pdf:
        # Process single PDF file
        extractor.process_pdf(args.pdf, args.output)
    elif args.dir:
        # Process all PDFs in directory
        extractor.process_directory(args.dir)
    else:
        print("Error: Please provide either --pdf or --dir argument")
        parser.print_help()

if __name__ == "__main__":
    main()