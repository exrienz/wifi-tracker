import csv
import io
from datetime import datetime
from flask import flash
from .models import WirelessScan

def parse_csv_data(csv_content, environment_id, user_id):
    """
    Parse CSV data and return a list of WirelessScan objects.
    Performs validation and deduplication.
    """
    scans = []
    errors = []
    duplicates = 0
    
    # Required CSV columns
    required_columns = ['bssid', 'ssid', 'quality', 'signal', 'channel', 'encryption', 'timestamp']
    
    try:
        # Use StringIO to read CSV content
        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file)
        
        # Validate headers
        if not reader.fieldnames:
            errors.append("CSV file appears to be empty or invalid")
            return scans, errors, duplicates
        
        missing_columns = set(required_columns) - set(reader.fieldnames)
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")
            return scans, errors, duplicates
        
        # Get existing scans for deduplication check
        existing_scans = WirelessScan.query.filter_by(environment_id=environment_id).all()
        existing_pairs = {(scan.bssid, scan.ssid) for scan in existing_scans}
        
        row_number = 0
        for row in reader:
            row_number += 1
            
            try:
                # Validate and clean data
                bssid = row['bssid'].strip().upper()
                ssid = row['ssid'].strip()
                
                # Basic BSSID format validation (MAC address)
                if not validate_bssid(bssid):
                    errors.append(f"Row {row_number}: Invalid BSSID format '{bssid}'")
                    continue
                
                # Check for duplicates
                if (bssid, ssid) in existing_pairs:
                    duplicates += 1
                    continue
                
                # Parse numeric fields
                try:
                    quality = int(row['quality']) if row['quality'].strip() else None
                    signal = int(row['signal']) if row['signal'].strip() else None
                    channel = int(row['channel']) if row['channel'].strip() else None
                except ValueError as e:
                    errors.append(f"Row {row_number}: Invalid numeric value - {str(e)}")
                    continue
                
                # Parse timestamp
                timestamp_str = row['timestamp'].strip()
                timestamp = parse_timestamp(timestamp_str)
                if not timestamp:
                    errors.append(f"Row {row_number}: Invalid timestamp format '{timestamp_str}'")
                    continue
                
                # Create WirelessScan object
                scan = WirelessScan(
                    environment_id=environment_id,
                    bssid=bssid,
                    ssid=ssid,
                    quality=quality,
                    signal=signal,
                    channel=channel,
                    encryption=row['encryption'].strip(),
                    timestamp=timestamp,
                    uploaded_by=user_id
                )
                
                scans.append(scan)
                existing_pairs.add((bssid, ssid))  # Prevent duplicates within the same upload
                
            except Exception as e:
                errors.append(f"Row {row_number}: Error processing row - {str(e)}")
                continue
    
    except Exception as e:
        errors.append(f"Error reading CSV file: {str(e)}")
    
    return scans, errors, duplicates

def validate_bssid(bssid):
    """Validate BSSID format (MAC address)"""
    if not bssid or len(bssid) != 17:
        return False
    
    # Check format: XX:XX:XX:XX:XX:XX
    parts = bssid.split(':')
    if len(parts) != 6:
        return False
    
    for part in parts:
        if len(part) != 2:
            return False
        try:
            int(part, 16)  # Check if valid hex
        except ValueError:
            return False
    
    return True

def parse_timestamp(timestamp_str):
    """Parse timestamp from various common formats"""
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y/%m/%d %H:%M:%S',
        '%d-%m-%Y %H:%M:%S',
        '%d/%m/%Y %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y/%m/%d %H:%M',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    
    return None

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"