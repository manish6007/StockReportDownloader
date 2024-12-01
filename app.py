import streamlit as st
import subprocess
import sys
import time
import os
import shutil
import re
import tempfile
from datetime import datetime
from pathlib import Path
import zipfile
import io

# Configure page
st.set_page_config(
    page_title="Company Analysis Tool",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_temp_dir():
    """Create and get temporary directory"""
    if 'temp_dir' not in st.session_state:
        st.session_state.temp_dir = tempfile.mkdtemp()
    return st.session_state.temp_dir

def validate_symbol(symbol):
    """Validate the input symbol"""
    if not symbol:
        raise ValueError("Company symbol cannot be empty")
        
    symbol = symbol.strip().upper()
    if not symbol.isalnum():
        raise ValueError("Company symbol should only contain letters and numbers")
        
    return symbol

def extract_file_paths(output):
    """Extract file paths from script output"""
    pdf_pattern = r'Generated report for.*?: (.*?\.pdf)'
    csv_pattern = r'Data successfully saved to (.*?\.csv)'
    
    files = []
    pdf_matches = re.findall(pdf_pattern, output)
    files.extend(pdf_matches)
    csv_matches = re.findall(csv_pattern, output)
    files.extend(csv_matches)
    
    return files

def cleanup_temp_files(temp_dir):
    """Clean up temporary files"""
    try:
        shutil.rmtree(temp_dir)
        st.session_state.temp_dir = tempfile.mkdtemp()
    except Exception as e:
        st.error(f"Error cleaning up temporary files: {str(e)}")

def create_zip_file(files, symbol):
    """Create a zip file containing all reports"""
    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in files:
                if os.path.exists(file_path):
                    # Get just the filename for the zip
                    file_name = os.path.basename(file_path)
                    # Add file to zip
                    zip_file.write(file_path, file_name)
        return zip_buffer
    except Exception as e:
        st.error(f"Error creating zip file: {str(e)}")
        return None

@st.cache_data(show_spinner=False)
def execute_script(script_name, symbol):
    """Execute a Python script with caching"""
    try:
        # Set environment variables for scripts
        temp_dir = get_temp_dir()
        analysis_dir = os.path.join(temp_dir, symbol)
        os.makedirs(analysis_dir, exist_ok=True)
        os.environ['ANALYSIS_OUTPUT_DIR'] = analysis_dir
        
        result = subprocess.run(
            [sys.executable, script_name, symbol],
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Error executing {script_name}:\nExit code: {e.returncode}\nError output: {e.stderr}"
        return False, error_msg
        
    except Exception as e:
        error_msg = f"Unexpected error executing {script_name}: {str(e)}"
        return False, error_msg

def main():
    st.title("📈 Company Analysis Tool")
    st.markdown("---")

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        debug_mode = st.checkbox("Enable Debug Mode", value=False)
        
        st.markdown("---")
        st.markdown("### 📁 Storage Info")
        st.info("Files are temporarily stored and will be deleted after download")

    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Analysis Form
        with st.form("analysis_form"):
            symbol = st.text_input("Enter Company Symbol:", 
                                 help="Example: AAPL, GOOGL, MSFT")
            analyze_button = st.form_submit_button("🔍 Analyze")

    if analyze_button:
        try:
            # Validate symbol
            symbol = validate_symbol(symbol)
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_container = st.empty()
            
            # Execute analysis scripts
            scripts = [
                'crawl_screener_generate_report_in_folder.py',
                'download_candledata_in_folder.py'
            ]
            
            success_count = 0
            outputs = []
            all_files = []
            
            for idx, script in enumerate(scripts):
                status_container.info(f"Running {script}...")
                success, output = execute_script(script, symbol)
                
                if success:
                    success_count += 1
                    if debug_mode:
                        st.success(f"✅ {script} completed successfully")
                    files = extract_file_paths(output)
                    all_files.extend(files)
                else:
                    st.error(f"❌ {script} failed")
                    if debug_mode:
                        st.code(output)
                
                outputs.append(output)
                progress_bar.progress((idx + 1) / len(scripts))
                time.sleep(0.5)
            
            # Process and display results
            if success_count == len(scripts):
                status_container.success(f"Analysis completed for {symbol}")
                
                if all_files:
                    st.markdown("### 📊 Generated Reports")
                    
                    # Create zip file of all reports
                    zip_buffer = create_zip_file(all_files, symbol)
                    
                    if zip_buffer:
                        # Prepare zip file for download
                        zip_buffer.seek(0)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        zip_filename = f"{symbol}_reports_{timestamp}.zip"
                        
                        # Download button for zip
                        st.download_button(
                            label="📥 Download All Reports (ZIP)",
                            data=zip_buffer.getvalue(),
                            file_name=zip_filename,
                            mime="application/zip",
                            on_click=cleanup_temp_files,
                            args=(st.session_state.temp_dir,)
                        )
                        
                        # Show files included in zip
                        with st.expander("📋 Files included in ZIP"):
                            for file_path in all_files:
                                if os.path.exists(file_path):
                                    st.text(f"📄 {os.path.basename(file_path)}")
                else:
                    st.warning("No reports were generated")
            
            # Debug information
            if debug_mode:
                with st.expander("🔍 Debug Information"):
                    st.markdown("### Script Outputs")
                    for script, output in zip(scripts, outputs):
                        st.markdown(f"**{script}:**")
                        st.code(output)
                        
        except ValueError as e:
            st.error(f"❌ {str(e)}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
            if debug_mode:
                st.exception(e)
        finally:
            progress_bar.empty()

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center'>
            <p>Made with ❤️ by Manish</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()