from flask import Flask, render_template, request, jsonify, send_file
import os
import json
from datetime import datetime, timedelta
import google.generativeai as genai
from dotenv import load_dotenv
import tempfile
from pathlib import Path

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Clean up old temp files on startup
def cleanup_temp_files():
    """Remove any leftover temporary audio files"""
    upload_folder = app.config['UPLOAD_FOLDER']
    if os.path.exists(upload_folder):
        for filename in os.listdir(upload_folder):
            if filename.startswith('temp_audio_'):
                try:
                    os.remove(os.path.join(upload_folder, filename))
                except:
                    pass  # Ignore errors during cleanup

cleanup_temp_files()

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Load knowledge base
def load_knowledge_base():
    kb_path = Path('knowledge_base.json')
    if kb_path.exists():
        with open(kb_path, 'r') as f:
            return json.load(f)
    return {}

def get_current_week_dates():
    """Get the date range for current week (Monday to Sunday)"""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday

def get_day_of_week_date(day_name):
    """Convert day name to actual date in current week"""
    days = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    
    day_offset = days.get(day_name.lower(), 0)
    target_date = monday + timedelta(days=day_offset)
    
    return target_date.strftime('%Y-%m-%d')

def create_system_prompt(knowledge_base):
    """Create system prompt for Gemini based on knowledge base"""
    monday, sunday = get_current_week_dates()
    
    # Extract project information
    projects_info = ""
    if "projects" in knowledge_base:
        projects_info = "AVAILABLE PROJECTS:\n"
        for proj in knowledge_base["projects"]:
            projects_info += f"- {proj['project_name']} (Code: {proj['project_code']}, Client: {proj['client_code']}, Task: {proj['task']}, Task ID: {proj['task_id']})\n"
    
    prompt = f"""You are an intelligent timesheet data extraction assistant. Your task is to analyze user input (text or transcribed speech) and extract structured timesheet entries.

CURRENT CONTEXT:
- Today's Date: {datetime.now().strftime('%Y-%m-%d (%A)')}
- Current Week: {monday.strftime('%Y-%m-%d')} (Monday) to {sunday.strftime('%Y-%m-%d')} (Sunday)

{projects_info}

IMPORTANT INSTRUCTIONS:
1. CAREFULLY analyze the input text to identify ALL work activities mentioned
2. For EACH activity, create a SEPARATE entry in the output array
3. Extract date/time information:
   - If user says "Monday", "Tuesday", etc. → use CURRENT WEEK dates
   - If user says "yesterday" → calculate yesterday's date
   - If user says "today" → use today's date
   - Convert all dates to YYYY-MM-DD format
4. Match activities to the correct project from the available projects list
5. Calculate duration in minutes (e.g., "8 hours" = 480 minutes, "3-4 hours" = 210 minutes (average))
6. The 'entry_date' field must NEVER be null - always include the date
7. Create a concise, grammatically correct comment (1-2 lines max) summarizing what was done
8. If multiple activities are mentioned for the same day, create MULTIPLE separate entries

OUTPUT FORMAT:
Return ONLY a valid JSON array. Each object should have this structure:
[
  {{
    "project_code": "matching project code from available projects",
    "client_code": "matching client code",
    "project_name": "matching project name",
    "task_name": "matching task name",
    "task_id": "matching task ID",
    "billing_classification": null,
    "entry_date": "YYYY-MM-DD",
    "start_time": null,
    "end_time": null,
    "duration_minutes": number (e.g., 480 for 8 hours, 240 for 4 hours),
    "comment": "Brief 1-2 line grammatically correct description of work done",
    "transcript_excerpt": "relevant excerpt from user's input"
  }}
]

CRITICAL RULES:
- entry_date must ALWAYS be in YYYY-MM-DD format, never null
- duration_minutes must be a number (convert hours to minutes: hours × 60)
- If duration is a range like "3-4 hours", use the average (3.5 hours = 210 minutes)
- Match project_code, client_code, project_name, task_name, and task_id from available projects
- If project is not found in the list, use the closest match or ask user to clarify
- Keep comments concise, professional, and grammatically correct
- transcript_excerpt should be the relevant portion of user's input for that activity
- Create separate entries for different days or different projects

Return ONLY the JSON array, no markdown formatting, no additional text."""
    
    return prompt

def transcribe_audio(audio_file_path):
    """Transcribe audio using Gemini"""
    try:
        import base64
        
        # Detect mime type from file extension
        file_ext = audio_file_path.lower().split('.')[-1]
        mime_types = {
            'webm': 'audio/webm',
            'mp3': 'audio/mp3',
            'wav': 'audio/wav',
            'ogg': 'audio/ogg',
            'm4a': 'audio/mp4',
            'mp4': 'audio/mp4'
        }
        mime_type = mime_types.get(file_ext, 'audio/webm')
        
        # Read and encode audio file
        with open(audio_file_path, 'rb') as f:
            audio_bytes = f.read()
        
        # Use Gemini to transcribe with inline data
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Create part with inline data
        audio_part = {
            "inline_data": {
                "mime_type": mime_type,
                "data": base64.b64encode(audio_bytes).decode('utf-8')
            }
        }
        
        response = model.generate_content([
            audio_part,
            "Transcribe this audio accurately. Return only the transcription text, nothing else."
        ])
        
        transcription = response.text.strip()
        return transcription
        
    except Exception as e:
        raise Exception(f"Transcription error: {str(e)}")

def process_with_gemini(text, knowledge_base):
    """Process text with Gemini to extract structured timesheet data"""
    try:
        system_prompt = create_system_prompt(knowledge_base)
        
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        full_prompt = f"{system_prompt}\n\nUSER INPUT:\n{text}\n\nExtract timesheet entries:"
        
        response = model.generate_content(full_prompt)
        result_text = response.text.strip()
        
        # Clean up response - remove markdown code blocks if present
        if result_text.startswith('```json'):
            result_text = result_text[7:]
        if result_text.startswith('```'):
            result_text = result_text[3:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        # Parse JSON
        structured_data = json.loads(result_text)
        
        # Add timestamp to each entry
        current_ts = datetime.utcnow().isoformat() + 'Z'
        for entry in structured_data:
            entry['ts'] = current_ts
        
        return structured_data
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse Gemini response as JSON: {str(e)}\nResponse: {result_text[:500]}")
    except Exception as e:
        raise Exception(f"Gemini processing error: {str(e)}")

def save_output(data):
    """Save structured data to CSV file"""
    import csv
    
    csv_path = Path('output_data.csv')
    
    # Check if file exists to determine if we need to write headers
    file_exists = csv_path.exists()
    
    # Define CSV columns
    fieldnames = [
        'entry_date', 'project_code', 'client_code', 'project_name', 
        'task_name', 'task_id', 'duration_minutes', 'comment', 
        'transcript_excerpt', 'billing_classification', 'start_time', 
        'end_time', 'ts'
    ]
    
    # Append to CSV
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        # Write header only if file is new
        if not file_exists or csv_path.stat().st_size == 0:
            writer.writeheader()
        
        # Write data rows
        for entry in data:
            # Ensure all fields exist
            row = {field: entry.get(field, '') for field in fieldnames}
            writer.writerow(row)
    
    return csv_path

@app.route('/')
def index():
    # Load projects for display
    kb = load_knowledge_base()
    projects = kb.get('projects', [])
    return render_template('index.html', projects=projects)

@app.route('/process', methods=['POST'])
def process():
    try:
        input_type = request.form.get('input_type')
        knowledge_base = load_knowledge_base()
        
        if not knowledge_base or 'projects' not in knowledge_base:
            return jsonify({'error': 'Knowledge base not found or invalid. Please ensure knowledge_base.json exists with projects data.'}), 400
        
        text_to_process = None
        
        if input_type == 'text':
            text_to_process = request.form.get('text_input')
            if not text_to_process:
                return jsonify({'error': 'No text input provided'}), 400
                
        elif input_type == 'recording':
            if 'audio_file' not in request.files:
                return jsonify({'error': 'No audio file provided'}), 400
            
            audio_file = request.files['audio_file']
            if audio_file.filename == '':
                return jsonify({'error': 'No audio file selected'}), 400
            
            # Save audio file temporarily with unique name
            import time
            timestamp = str(time.time()).replace('.', '_')
            temp_filename = f'temp_audio_{timestamp}.webm'
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
            
            try:
                audio_file.save(temp_path)
                
                # Transcribe audio
                text_to_process = transcribe_audio(temp_path)
                
            except Exception as e:
                # Clean up on error
                if os.path.exists(temp_path):
                    try:
                        time.sleep(1)  # Wait a moment before deleting
                        os.remove(temp_path)
                    except:
                        pass  # Ignore cleanup errors
                raise e
            
            finally:
                # Clean up temp file with retry logic
                if os.path.exists(temp_path):
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            time.sleep(1)  # Wait before deleting
                            os.remove(temp_path)
                            break
                        except PermissionError:
                            if attempt < max_retries - 1:
                                time.sleep(2)  # Wait longer on retry
                            else:
                                # If still can't delete, it will be cleaned up later
                                pass
        
        if not text_to_process:
            return jsonify({'error': 'No input to process'}), 400
        
        # Process with Gemini
        structured_data = process_with_gemini(text_to_process, knowledge_base)
        
        # Save to output file
        output_path = save_output(structured_data)
        
        return jsonify({
            'success': True,
            'transcription': text_to_process if input_type == 'recording' else None,
            'structured_data': structured_data,
            'entry_count': len(structured_data),
            'message': f'Successfully processed {len(structured_data)} timesheet entries and saved to {output_path}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download')
def download():
    csv_path = Path('output_data.csv')
    if csv_path.exists():
        return send_file(csv_path, as_attachment=True, download_name='timesheet_entries.csv', mimetype='text/csv')
    return jsonify({'error': 'Output file not found'}), 404

@app.route('/clear', methods=['POST'])
def clear_output():
    csv_path = Path('output_data.csv')
    if csv_path.exists():
        os.remove(csv_path)
    return jsonify({'success': True, 'message': 'Output file cleared successfully'})

@app.route('/projects')
def get_projects():
    kb = load_knowledge_base()
    return jsonify(kb.get('projects', []))

if __name__ == '__main__':
    app.run(debug=True, port=5000)