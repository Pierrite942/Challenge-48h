# Challenge-48h

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. **Create a virtual environment** (optional but recommended):
```bash
python -m venv .venv
```

2. **Activate the virtual environment**:
   - On Windows:
   ```bash
   .venv\Scripts\activate
   ```
   - On macOS/Linux:
   ```bash
   source .venv/bin/activate
   ```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**:
Create a `.env` file in the root directory with the following variables:
```
FLASK_SECRET_KEY=your-secret-key-here
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=ynook_db
```

## Running the Server

To launch the Python Flask server:

```bash
python app.py
```

The server will start on `http://localhost:5000` by default.

If you're in a virtual environment:
```bash
.venv\Scripts\python.exe app.py
```

## Project Structure

- `app.py` - Main Flask application
- `requirements.txt` - Python dependencies
- `html/` - HTML templates
- `css/` - CSS stylesheets
- `ia/` - AI/API related modules
- `image/` - Image assets