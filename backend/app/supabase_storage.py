"""
Supabase Storage Client for PNJ Cleaning
Handles file uploads to Supabase Storage bucket
"""
import os
from typing import BinaryIO
from .supabase_client import supabase

BUCKET_NAME = "pnj-uploads"

def upload_file(file_content: bytes, file_path: str) -> str:
    """
    Upload a file to Supabase Storage
    
    Args:
        file_content: Binary content of the file
        file_path: Path within the bucket (e.g., "reports/2024/image.jpg")
    
    Returns:
        Public URL of the uploaded file
    """
    try:
        # Upload to Supabase Storage
        result = supabase.storage.from_(BUCKET_NAME).upload(
            file_path,
            file_content,
            file_options={"content-type": "image/jpeg"}  # Adjust based on file type
        )
        
        # Get public URL
        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
        
        return public_url
    except Exception as e:
        print(f"Error uploading to Supabase Storage: {e}")
        raise


def delete_file(file_path: str) -> bool:
    """
    Delete a file from Supabase Storage
    
    Args:
        file_path: Path within the bucket
    
    Returns:
        True if successful
    """
    try:
        supabase.storage.from_(BUCKET_NAME).remove([file_path])
        return True
    except Exception as e:
        print(f"Error deleting from Supabase Storage: {e}")
        return False


def get_file_url(file_path: str) -> str:
    """
    Get the public URL for a file
    
    Args:
        file_path: Path within the bucket
    
    Returns:
        Public URL
    """
    return supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
