import streamlit as st
import subprocess
import sys
import time
import os
import shutil
import re
from pathlib import Path

def validate_symbol(symbol):
    """
    Validate the input symbol
    
    Parameters:
    symbol (str): Company symbol
    
    Returns:
    str: Validated symbol
    """
    if not symbol:
        raise ValueError("Company symbol cannot be empty")
        
    symbol = symbol.strip().upper()
    if not symbol.isalnum():
        raise ValueError("Company symbol should only contain letters and numbers")
        
    return symbol

def extract_file_paths(output):
    """
    Extract file paths from script output
    
    Parameters:
    output (str): Script output text
    
    Returns:
    list: List of file paths found in the output
    """
    # Pattern for PDF files
    pdf_pattern = r'Generated report for.*?: (.*?\.pdf)'
    # Pattern for CSV files
    csv_pattern = r'Data successfully saved to (.*?\.csv)'
    
    files = []
    
    # Find PDF files
    pdf_matches = re.findall(pdf_pattern, output)
    files.extend(pdf_matches)
    
    # Find CSV files
    csv_matches = re.findall(csv_pattern, output)
    files.extend(csv_matches)
    
    return files

def execute_script(script_name, symbol):
    """
    Execute a Python script with the given symbol argument
    
    Parameters:
    script_name (str): Name of the script to execute
    symbol (str): Company symbol to pass as argument
    
    Returns:
    bool, str: Success status and output message
    """
    try:
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

def copy_files_to_target(files, symbol, target_dir):
    """
    Copy files to target directory in a stock-specific folder
    
    Parameters:
    files (list): List of source file paths
    symbol (str): Stock symbol
    target_dir (str): Target directory path
    
    Returns:
    list: List of copied file paths
    """
    # Create stock-specific folder in target directory
    stock_folder = os.path.join(target_dir, symbol)
    os.makedirs(stock_folder, exist_ok=True)
    
    copied_files = []
    for src_path in files:
        if os.path.exists(src_path):
            # Get file name and create target path
            file_name = os.path.basename(src_path)
            dst_path = os.path.join(stock_folder, file_name)
            
            try:
                shutil.copy2(src_path, dst_path)
                copied_files.append(dst_path)
            except Exception as e:
                st.error(f"Error copying {file_name}: {str(e)}")
                
    return copied_files

def main():
    st.set_page_config(page_title="Company Analysis Tool", layout="wide")
    
    st.title("Company Analysis Tool")
    st.markdown("---")
    
    # Target directory input
    target_dir = st.text_input(
        "Enter target directory path for reports:",
        value=os.path.expanduser("~\\Documents\\StockReports"),
        help="Reports will be organized in stock-specific folders within this directory"
    )
    
    # Create a form for input
    with st.form("analysis_form"):
        symbol = st.text_input("Enter company symbol:")
        submit_button = st.form_submit_button("Analyze")
    
    if submit_button:
        try:
            # Validate symbol and target directory
            symbol = validate_symbol(symbol)
            if not os.path.exists(target_dir):
                try:
                    os.makedirs(target_dir)
                    st.success(f"Created target directory: {target_dir}")
                except Exception as e:
                    st.error(f"Error creating target directory: {str(e)}")
                    return
            
            # Create a progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Define scripts to execute
            scripts = [
                'crawl_screener_generate_report_in_folder.py',
                'download_candledata_in_folder.py'
            ]
            
            # Execute each script
            success_count = 0
            outputs = []
            all_files = []
            
            for idx, script in enumerate(scripts):
                status_text.text(f"Executing {script}...")
                success, output = execute_script(script, symbol)
                
                if success:
                    success_count += 1
                    st.success(f"Successfully executed {script}")
                    # Extract file paths from output
                    files = extract_file_paths(output)
                    all_files.extend(files)
                else:
                    st.error(f"Failed to execute {script}")
                
                outputs.append(output)
                progress_bar.progress((idx + 1) / len(scripts))
                time.sleep(1)
            
            # Final status
            if success_count == len(scripts):
                st.success(f"Successfully completed all analyses for {symbol}")
                
                if all_files:
                    # Copy files to target location
                    st.markdown("---")
                    st.subheader("Copying Reports")
                    
                    copied_files = copy_files_to_target(all_files, symbol, target_dir)
                    
                    if copied_files:
                        st.success(f"Successfully copied {len(copied_files)} files to:")
                        st.code(os.path.join(target_dir, symbol))
                        
                        # Display copied files
                        with st.expander("View Copied Files"):
                            for file_path in copied_files:
                                st.text(f"📄 {os.path.basename(file_path)}")
                    else:
                        st.error("Failed to copy any files to target location")
                else:
                    st.warning("No reports were found in the script output")
            else:
                st.warning(f"Completed with some errors. {success_count} out of {len(scripts)} scripts succeeded for {symbol}")
            
            # Display detailed output in expander
            with st.expander("View Detailed Output"):
                for script, output in zip(scripts, outputs):
                    st.markdown(f"**Output from {script}:**")
                    st.text(output)
                
        except ValueError as e:
            st.error(f"Error: {str(e)}")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            st.exception(e)

if __name__ == "__main__":
    main()